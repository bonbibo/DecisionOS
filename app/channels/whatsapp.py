"""Meta (WhatsApp) Cloud API channel.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks

Inbound flow, routed by the sender's phone number:
  - has an active (non-close) Case as its counterparty_contact -> negotiation:
    fed through app.orchestrator.run_turn; an approved draft is queued in
    outbound_queue (audience=counterparty) for human approval, and a short
    status update is queued for the case's own user (audience=client).
  - no active Case -> intake: fed through app.intake.run_intake_turn. These
    replies go straight back to the user (not queued) since they're a
    conversational onboarding chat with our own customer, not a negotiation
    draft headed to the counterparty.

Nothing negotiation-facing is ever sent automatically; only
POST /review/{id}/approve sends.
"""

import hashlib
import hmac
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.engine import load_profiles, load_tactics, record_message
from app.intake import run_intake_turn
from app.llm import AnthropicSubagentClient
from app.models import (
    AudienceEnum,
    Case,
    ChannelEnum,
    DirectionEnum,
    Message,
    MessageKindEnum,
    OutboundQueueItem,
    OutboundStatusEnum,
    StateEnum,
    User,
)
from app.orchestrator import TurnResult, run_turn

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/channels/whatsapp", tags=["whatsapp"])

GRAPH_API_BASE = "https://graph.facebook.com/v20.0"
VAULT_DIR = "vault"
THREAD_HISTORY_LIMIT = 10


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    """Meta's subscription verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=status.HTTP_403_FORBIDDEN)


def _has_valid_signature(body: bytes, signature_header: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 header (HMAC-SHA256 of the raw body
    keyed with WHATSAPP_APP_SECRET) so only Meta can feed us events."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(settings.whatsapp_app_secret.encode(), body, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Inbound WhatsApp events (messages, statuses, etc.)."""
    body = await request.body()
    if not _has_valid_signature(body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(status_code=401, detail="invalid webhook signature")

    payload = await request.json()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                await _route_inbound_message(db, message)

    return {"status": "received"}


def _find_active_case(db: Session, sender: str) -> Case | None:
    return db.execute(
        select(Case)
        .where(
            Case.channel == ChannelEnum.whatsapp,
            Case.counterparty_contact == sender,
            Case.state != StateEnum.close,
        )
        .order_by(Case.created_at.desc())
    ).scalars().first()


async def _route_inbound_message(db: Session, message: dict) -> None:
    sender = message.get("from")
    msg_type = message.get("type")
    text = message.get("text", {}).get("body") if msg_type == "text" else None

    if not text:
        logger.info("WhatsApp inbound from=%s type=%s — no text body, skipping", sender, msg_type)
        return

    case = _find_active_case(db, sender)
    if case is not None:
        _handle_negotiation_message(db, case, sender, text, message)
    else:
        await _handle_intake_message(db, sender, text, message)


def _status_message_for(result: TurnResult, case: Case) -> str:
    if result.status == "escalated":
        return (
            "Görüşmede bir noktayı ekibimize danışıyoruz, kısa süre içinde güncelleme geleceğiz. / "
            "We're checking one detail with our team on your negotiation — an update is coming shortly."
        )
    return (
        f"Görüşme devam ediyor ({case.state.value}). Yeni gelişme oldu, onayınızı bekliyoruz. / "
        f"Negotiation in progress ({case.state.value}). There's a new development awaiting your review."
    )


def _handle_negotiation_message(db: Session, case: Case, sender: str, text: str, raw_message: dict) -> None:
    record_message(
        case,
        channel=ChannelEnum.whatsapp,
        direction=DirectionEnum.inbound,
        content=text,
        sender=sender,
        raw_payload=raw_message,
        user=case.user,
    )
    db.flush()

    thread = [
        {"direction": m.direction.value, "content": m.content}
        for m in case.messages[-THREAD_HISTORY_LIMIT:]
    ]
    tactics = load_tactics(VAULT_DIR)
    profiles = [
        {"profile_id": p.profile_id, "ad": p.ad, "body": p.body} for p in load_profiles(VAULT_DIR)
    ]

    client = AnthropicSubagentClient(case_id=case.id, db=db, user_id=case.user_id)
    result = run_turn(case, client, incoming_message=text, thread=thread, tactics=tactics, profiles=profiles)

    if result.status == "approved" and result.draft:
        db.add(
            OutboundQueueItem(
                case=case,
                channel=ChannelEnum.whatsapp,
                recipient=sender,
                message=result.draft["message"],
                tactic_used=result.draft.get("tactic_used"),
                status=OutboundStatusEnum.pending_approval,
                audience=AudienceEnum.counterparty,
            )
        )

    if case.user_id:
        db.add(
            OutboundQueueItem(
                case=case,
                channel=ChannelEnum.whatsapp,
                recipient=case.user.phone,
                message=_status_message_for(result, case),
                status=OutboundStatusEnum.pending_approval,
                audience=AudienceEnum.client,
            )
        )

    db.commit()


async def _handle_intake_message(db: Session, sender: str, text: str, raw_message: dict) -> None:
    user = db.execute(select(User).where(User.phone == sender)).scalars().first()
    if user is None:
        user = User(phone=sender)
        db.add(user)
        db.flush()

    inbound = record_message(
        None,
        channel=ChannelEnum.whatsapp,
        direction=DirectionEnum.inbound,
        content=text,
        sender=sender,
        raw_payload=raw_message,
        user=user,
        kind=MessageKindEnum.intake,
    )
    db.add(inbound)
    db.flush()

    thread = [
        {"direction": m.direction.value, "content": m.content}
        for m in reversed(
            db.execute(
                select(Message)
                .where(Message.user_id == user.id, Message.kind == MessageKindEnum.intake)
                .order_by(Message.created_at.desc())
                .limit(THREAD_HISTORY_LIMIT)
            ).scalars().all()
        )
    ]
    tactics = load_tactics(VAULT_DIR)

    client = AnthropicSubagentClient(case_id=None, db=db, user_id=user.id)
    result = run_intake_turn(user, client, incoming_message=text, thread=thread, tactics=tactics)

    if result.status == "escalated":
        logger.error("Intake escalated for user=%s: %s", user.id, result.escalation_reason)
        db.commit()
        return

    if result.case is not None:
        db.add(result.case)

    db.commit()

    if result.reply:
        await send_text_message(sender, result.reply)


async def send_text_message(to: str, body: str) -> dict:
    """Send a free-form text message via the Cloud API.

    Called directly for intake replies (low-risk, our own customer) and from
    POST /review/{id}/approve for negotiation/status drafts — never
    automatically for anything headed to a counterparty. Requires an active
    24h customer service window or an approved template outside of it.
    Returns the Graph API response JSON.
    """
    url = f"{GRAPH_API_BASE}/{settings.whatsapp_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
