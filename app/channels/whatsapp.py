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
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.channels import email
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
from app.orchestrator import TurnResult, run_turn, status_message_for
from app.payments import handle_turn_outcome

OPT_IN_WINDOW = timedelta(hours=24)

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
    handle_turn_outcome(case, vault_dir=VAULT_DIR)

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
                message=status_message_for(result, case),
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

    if result.case is not None:
        # Email-first initial contact (Package H) — no-op if the case has no
        # counterparty_email. Never blocks the reply to our own customer.
        email.send_initial_contact_email(result.case)

    if result.reply:
        await send_text_message(sender, result.reply, db)


class OptInRequiredError(Exception):
    """Raised by send_text_message when `to` has no valid opt-in — see
    _has_valid_opt_in. The Package H guard: this is checked unconditionally
    (not just for counterparty-audience sends) so there is exactly one
    choke point where a WhatsApp message can leave the system at all."""

    def __init__(self, to: str):
        self.to = to
        super().__init__(f"no valid WhatsApp opt-in for {to}")


def _has_valid_opt_in(db: Session, recipient: str) -> bool:
    """True iff `recipient` has sent us an inbound WhatsApp message within
    Meta's own 24h customer-service window — the one real opt-in signal a
    business-initiated message can rely on (see docs/MASTER-SPEC-v3.md
    Package H). A recipient who has only visited the /optin/{case_id}
    landing page (OptIn.method=email_link_click) but never actually
    messaged us does NOT pass this — that's an audit record, not consent
    to receive a business-initiated message yet."""
    cutoff = datetime.now(timezone.utc) - OPT_IN_WINDOW
    return (
        db.execute(
            select(Message.id)
            .where(
                Message.sender == recipient,
                Message.direction == DirectionEnum.inbound,
                Message.channel == ChannelEnum.whatsapp,
                Message.created_at >= cutoff,
            )
            .limit(1)
        ).first()
        is not None
    )


async def send_text_message(to: str, body: str, db: Session) -> dict:
    """Send a free-form text message via the Cloud API.

    Called directly for intake replies (always passes the guard below,
    since the recipient just messaged us to trigger the reply) and from
    POST /review/{id}/approve for negotiation/status drafts — never
    automatically for anything headed to a counterparty. Requires an active
    24h customer service window or an approved template outside of it.
    Returns the Graph API response JSON.
    """
    if not _has_valid_opt_in(db, to):
        raise OptInRequiredError(to)

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
