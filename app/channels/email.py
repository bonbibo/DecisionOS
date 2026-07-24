"""Gmail API channel stub.

Docs: https://developers.google.com/gmail/api/guides

Gmail has no direct "webhook" delivery like WhatsApp: inbound mail is
surfaced either by polling `users.messages.list` or by registering a
`watch()` that pushes notifications through Cloud Pub/Sub, which then
calls back into `/channels/email/webhook`. Both entry points are stubbed
here; only the plumbing (auth, routing) is wired up.
"""

import base64
import logging
from email.mime.text import MIMEText
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Request

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/channels/email", tags=["email"])

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


@lru_cache
def get_gmail_service() -> Any:
    """Build an authorized Gmail API client from the configured OAuth2 refresh token.

    Imports google-api-python-client lazily so the rest of the app can be
    imported/tested without the Google client libraries installed.
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    credentials = Credentials(
        token=None,
        refresh_token=settings.gmail_refresh_token,
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=GMAIL_SCOPES,
    )
    return build("gmail", "v1", credentials=credentials)


@router.post("/webhook")
async def receive_pubsub_push(request: Request) -> dict:
    """Cloud Pub/Sub push endpoint fed by a Gmail `users.watch()` subscription.

    The push envelope carries a base64-encoded `{emailAddress, historyId}`
    payload; the actual message content must be fetched separately via
    `users.history.list` / `users.messages.get`.

    TODO: decode the envelope, call `_sync_new_messages`, and dispatch
    each new message into app.engine via a DB session.
    """
    envelope = await request.json()
    logger.info("Gmail push notification received: %s", envelope)
    return {"status": "received"}


def _sync_new_messages(history_id: str) -> list[dict]:
    """Fetch messages newer than `history_id` for the watched mailbox.

    Stub: wraps `users.history.list`. Returns raw Gmail message resources.
    """
    service = get_gmail_service()
    history = (
        service.users()
        .history()
        .list(userId="me", startHistoryId=history_id, historyTypes=["messageAdded"])
        .execute()
    )
    return history.get("history", [])


def send_email(to: str, subject: str, body: str, thread_id: str | None = None) -> dict:
    """Send a plain-text email reply via the Gmail API."""
    service = get_gmail_service()

    mime_message = MIMEText(body)
    mime_message["to"] = to
    mime_message["from"] = settings.gmail_sender_address
    mime_message["subject"] = subject

    raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
    body_payload: dict[str, Any] = {"raw": raw}
    if thread_id:
        body_payload["threadId"] = thread_id

    return service.users().messages().send(userId="me", body=body_payload).execute()
