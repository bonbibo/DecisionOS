"""Meta (WhatsApp) Cloud API channel.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks

Inbound flow: an incoming text message is matched to the sender's active
Case (by phone number), fed through app.orchestrator.run_turn, and — if
Kritik approves the draft — queued in outbound_queue for human approval.
Nothing is ever sent automatically; only POST /review/{id}/approve sends.
"""

import logging

import httpx
from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.engine import load_profiles, load_tactics, record_message
from app.llm import AnthropicSubagentClient
from app.models import Case, ChannelEnum, DirectionEnum, OutboundQueueItem, OutboundStatusEnum, StateEnum
from app.orchestrator import run_turn

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


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Inbound WhatsApp events (messages, statuses, etc.)."""
    payload = await request.json()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                _handle_inbound_message(db, message)

    return {"status": "received"}


def _handle_inbound_message(db: Session, message: dict) -> None:
    sender = message.get("from")
    msg_type = message.get("type")
    text = message.get("text", {}).get("body") if msg_type == "text" else None

    if not text:
        logger.info("WhatsApp inbound from=%s type=%s — no text body, skipping", sender, msg_type)
        return

    case = db.execute(
        select(Case)
        .where(
            Case.channel == ChannelEnum.whatsapp,
            Case.counterparty_contact == sender,
            Case.state != StateEnum.close,
        )
        .order_by(Case.created_at.desc())
    ).scalars().first()

    if case is None:
        logger.warning("WhatsApp inbound from unknown sender=%s — no active case, dropping", sender)
        return

    record_message(
        case,
        channel=ChannelEnum.whatsapp,
        direction=DirectionEnum.inbound,
        content=text,
        sender=sender,
        raw_payload=message,
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

    client = AnthropicSubagentClient(case_id=case.id, db=db)
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
            )
        )

    db.commit()


async def send_text_message(to: str, body: str) -> dict:
    """Send a free-form text message via the Cloud API.

    Only called from POST /review/{id}/approve — never automatically.
    Requires an active 24h customer service window or an approved template
    outside of it. Returns the Graph API response JSON.
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
