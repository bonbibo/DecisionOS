"""Human-in-the-loop review queue for Kritik-approved drafts (V1: plain REST).

Every draft run_turn approves lands in outbound_queue as pending_approval —
nothing is sent automatically. A human calls one of these three endpoints;
only approve actually sends (currently WhatsApp only). Every endpoint here
requires `Authorization: Bearer <REVIEW_TOKEN>` — anyone who finds the
deployed URL can otherwise approve/send on the agent's behalf.

Also exposes the other half of the human-in-the-loop story: a Kritik
ESCALATE stops the turn and asks a human a question (see
app.orchestrator._escalate / .resume_after_escalation) rather than guessing;
POST /review/case/{id}/answer is how the human's answer gets fed back in.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.channels import whatsapp
from app.config import get_settings
from app.database import get_db
from app.engine import load_tactics
from app.llm import AnthropicSubagentClient
from app.models import AudienceEnum, Case, ChannelEnum, OutboundQueueItem, OutboundStatusEnum
from app.orchestrator import resume_after_escalation, status_message_for
from app.payments import PreAuthRequiredError, handle_turn_outcome, require_pre_auth
from app.schemas import (
    CaseAnswerRequest,
    CaseRead,
    OutboundQueueRead,
    ReviewApproveRequest,
    ReviewEditRequest,
    ReviewRejectRequest,
)


def require_review_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {get_settings().review_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="missing or invalid bearer token")


router = APIRouter(prefix="/review", tags=["review"], dependencies=[Depends(require_review_token)])

_ACTIONABLE_STATUSES = {OutboundStatusEnum.pending_approval, OutboundStatusEnum.edited}
VAULT_DIR = "vault"
THREAD_HISTORY_LIMIT = 10


def _get_item(db: Session, msg_id: uuid.UUID) -> OutboundQueueItem:
    item = db.get(OutboundQueueItem, msg_id)
    if item is None:
        raise HTTPException(status_code=404, detail="outbound queue item not found")
    return item


def _get_case(db: Session, case_id: uuid.UUID) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    return case


@router.post("/{msg_id}/approve", response_model=OutboundQueueRead)
async def approve(msg_id: uuid.UUID, body: ReviewApproveRequest, db: Session = Depends(get_db)) -> OutboundQueueItem:
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    if item.channel is not ChannelEnum.whatsapp:
        raise HTTPException(status_code=501, detail=f"sending for channel '{item.channel.value}' isn't wired up yet")

    if item.audience is AudienceEnum.counterparty:
        try:
            require_pre_auth(item.case, vault_dir=VAULT_DIR)
        except PreAuthRequiredError as exc:
            raise HTTPException(status_code=409, detail="payment pre-authorization required") from exc

    try:
        await whatsapp.send_text_message(item.recipient, item.message, db)
    except whatsapp.OptInRequiredError as exc:
        raise HTTPException(status_code=409, detail=f"no valid WhatsApp opt-in for {exc.to}") from exc

    now = datetime.now(timezone.utc)
    item.status = OutboundStatusEnum.sent
    item.sent_at = now
    item.reviewed_at = now
    item.reviewed_by = body.reviewed_by
    db.commit()
    db.refresh(item)
    return item


@router.post("/{msg_id}/edit", response_model=OutboundQueueRead)
def edit(msg_id: uuid.UUID, body: ReviewEditRequest, db: Session = Depends(get_db)) -> OutboundQueueItem:
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    item.message = body.message
    item.status = OutboundStatusEnum.edited
    item.reviewed_at = datetime.now(timezone.utc)
    item.reviewed_by = body.reviewed_by
    db.commit()
    db.refresh(item)
    return item


@router.post("/{msg_id}/reject", response_model=OutboundQueueRead)
def reject(msg_id: uuid.UUID, body: ReviewRejectRequest, db: Session = Depends(get_db)) -> OutboundQueueItem:
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    item.status = OutboundStatusEnum.rejected
    item.reviewed_at = datetime.now(timezone.utc)
    item.reviewed_by = body.reviewed_by
    db.commit()
    db.refresh(item)
    return item


@router.post("/case/{case_id}/answer", response_model=CaseRead)
def answer_escalation(case_id: uuid.UUID, body: CaseAnswerRequest, db: Session = Depends(get_db)) -> Case:
    """Resume an ESCALATEd case with an operator's answer/instruction.

    Re-runs the turn that escalated (app.orchestrator.resume_after_escalation)
    with the answer attached as HUMAN_GUIDANCE. Queueing afterwards mirrors
    a normal WhatsApp turn exactly: an approved draft goes to
    outbound_queue (audience=counterparty); a status update for the case's
    own user is queued too, whatever the outcome (still escalated or not).
    """
    case = _get_case(db, case_id)
    if not case.escalated:
        raise HTTPException(status_code=409, detail="case is not escalated")

    thread = [
        {"direction": m.direction.value, "content": m.content}
        for m in case.messages[-THREAD_HISTORY_LIMIT:]
    ]
    tactics = load_tactics(VAULT_DIR)
    client = AnthropicSubagentClient(case_id=case.id, db=db, user_id=case.user_id)

    result = resume_after_escalation(
        case, client, body.answer, thread, tactics, vault_dir=VAULT_DIR, answered_by=body.reviewed_by
    )
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
    db.refresh(case)
    return case
