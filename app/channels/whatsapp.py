"""Meta (WhatsApp) Cloud API channel stub.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks

This module wires the webhook verification handshake and the inbound
message endpoint. Payload parsing follows the Cloud API's `messages`
webhook shape; the actual persistence / engine dispatch is left as a
TODO so it can be filled in alongside the DB session plumbing.
"""

import logging

import httpx
from fastapi import APIRouter, Query, Request, Response, status

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/channels/whatsapp", tags=["whatsapp"])

GRAPH_API_BASE = "https://graph.facebook.com/v20.0"


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
async def receive_webhook(request: Request) -> dict:
    """Inbound WhatsApp events (messages, statuses, etc.)."""
    payload = await request.json()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                _handle_inbound_message(value, message)

    return {"status": "received"}


def _handle_inbound_message(value: dict, message: dict) -> None:
    """Parse a single inbound WhatsApp message.

    TODO: look up (or create) the Case by the sender's phone number,
    call app.engine.record_message(...) + NegotiationEngine to advance
    state, and persist via a DB session.
    """
    sender = message.get("from")
    msg_type = message.get("type")
    text = message.get("text", {}).get("body") if msg_type == "text" else None
    logger.info("WhatsApp inbound from=%s type=%s text=%r", sender, msg_type, text)


async def send_text_message(to: str, body: str) -> dict:
    """Send a free-form text message via the Cloud API.

    Stub: requires an active 24h customer service window or an approved
    template outside of it. Returns the Graph API response JSON.
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
