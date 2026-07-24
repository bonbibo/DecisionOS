"""Web chat channel: our own customers talking to the agent directly through
a browser instead of WhatsApp.

Inbound flow mirrors app.channels.whatsapp, keyed by the authenticated
User (not a phone number) since the web session already identifies our
customer:
  - user has an active (non-close) Case -> negotiation: fed through
    app.orchestrator.run_turn. The counterparty-facing draft (if approved)
    is queued in outbound_queue (audience=counterparty, channel=whatsapp,
    since the counterparty is only ever reached over WhatsApp) for human
    approval — unchanged from the WhatsApp flow. The client-facing status
    update is *not* queued: this channel is synchronous, so it's returned
    inline in the HTTP response instead.
  - no active Case -> intake: fed through app.intake.run_intake_turn, reply
    returned inline.

POST /web/register issues a bearer session_token for POST /web/chat and
GET /web/case/{id}/timeline. V1 has no email/phone verification —
registering is enough, same trust model as WhatsApp (anyone who can text
the number is treated as that phone's owner).
"""

import logging
import secrets
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.channels import email
from app.database import get_db
from app.engine import load_tactics, record_message
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
from app.orchestrator import run_turn, status_message_for
from app.payments import handle_turn_outcome
from app.schemas import (
    CaseTimelineRead,
    WebChatRequest,
    WebChatResponse,
    WebRegisterRequest,
    WebRegisterResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web", tags=["web"])

VAULT_DIR = "vault"
THREAD_HISTORY_LIMIT = 10

_INTAKE_ESCALATION_REPLY = (
    "Bir noktayı ekibimize danışıyoruz, kısa süre içinde döneceğiz. / "
    "We're checking one detail with our team — we'll get back to you shortly."
)


def require_web_session(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer session token")
    token = authorization.removeprefix("Bearer ")
    user = db.execute(select(User).where(User.web_session_token == token)).scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="invalid or expired session token")
    return user


@router.post("/register", response_model=WebRegisterResponse)
def register(payload: WebRegisterRequest, db: Session = Depends(get_db)) -> WebRegisterResponse:
    user = db.execute(select(User).where(User.phone == payload.phone)).scalars().first()
    token = secrets.token_urlsafe(32)
    if user is None:
        user = User(phone=payload.phone, email=payload.email, name=payload.name, web_session_token=token)
        db.add(user)
    else:
        user.email = payload.email
        if payload.name is not None:
            user.name = payload.name
        user.web_session_token = token
    db.commit()
    db.refresh(user)
    return WebRegisterResponse(user_id=user.id, session_token=token)


def _find_active_case(db: Session, user: User) -> Case | None:
    return db.execute(
        select(Case)
        .where(Case.user_id == user.id, Case.state != StateEnum.close)
        .order_by(Case.created_at.desc())
    ).scalars().first()


def _handle_negotiation_message(db: Session, case: Case, user: User, text: str) -> WebChatResponse:
    record_message(
        case,
        channel=ChannelEnum.web,
        direction=DirectionEnum.inbound,
        content=text,
        sender=str(user.id),
        user=user,
    )
    db.flush()

    thread = [
        {"direction": m.direction.value, "content": m.content}
        for m in case.messages[-THREAD_HISTORY_LIMIT:]
    ]
    tactics = load_tactics(VAULT_DIR)

    client = AnthropicSubagentClient(case_id=case.id, db=db, user_id=user.id)
    result = run_turn(case, client, incoming_message=text, thread=thread, tactics=tactics)
    handle_turn_outcome(case, vault_dir=VAULT_DIR)

    if result.status == "approved" and result.draft:
        db.add(
            OutboundQueueItem(
                case=case,
                channel=ChannelEnum.whatsapp,
                recipient=case.counterparty_contact,
                message=result.draft["message"],
                tactic_used=result.draft.get("tactic_used"),
                status=OutboundStatusEnum.pending_approval,
                audience=AudienceEnum.counterparty,
            )
        )

    reply = status_message_for(result, case)
    db.commit()
    return WebChatResponse(reply=reply, case_id=case.id, state=case.state, escalated=case.escalated)


def _handle_intake_message(db: Session, user: User, text: str) -> WebChatResponse:
    record_message(
        None,
        channel=ChannelEnum.web,
        direction=DirectionEnum.inbound,
        content=text,
        sender=str(user.id),
        user=user,
        kind=MessageKindEnum.intake,
    )
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
        logger.error("Web intake escalated for user=%s: %s", user.id, result.escalation_reason)
        db.commit()
        return WebChatResponse(reply=_INTAKE_ESCALATION_REPLY, escalated=True)

    if result.case is not None:
        db.add(result.case)
    db.commit()

    if result.case is not None:
        # Email-first initial contact (Package H) — no-op if the case has no
        # counterparty_email.
        email.send_initial_contact_email(result.case)

    case_id = result.case.id if result.case else None
    state = result.case.state if result.case else None
    return WebChatResponse(reply=result.reply, case_id=case_id, state=state)


@router.post("/chat", response_model=WebChatResponse)
def chat(
    payload: WebChatRequest, user: User = Depends(require_web_session), db: Session = Depends(get_db)
) -> WebChatResponse:
    case = _find_active_case(db, user)
    if case is not None:
        return _handle_negotiation_message(db, case, user, payload.message)
    return _handle_intake_message(db, user, payload.message)


@router.get("/case/{case_id}/timeline", response_model=CaseTimelineRead)
def timeline(
    case_id: uuid.UUID, user: User = Depends(require_web_session), db: Session = Depends(get_db)
) -> Case:
    case = db.get(Case, case_id)
    if case is None or case.user_id != user.id:
        raise HTTPException(status_code=404, detail="case not found")
    return case
