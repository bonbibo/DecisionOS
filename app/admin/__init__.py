"""Server-rendered operator panel (V1: plain Jinja + HTML forms, no JS build step).

Same trust boundary as app.review: HTTP Basic auth checked against
REVIEW_TOKEN (username is not checked, only the password — the token is
the credential, same as the Bearer token on /review/*). The panel talks to
the negotiation-side of the system by duplicating review.py's small
approve/edit/reject state transitions rather than importing them, so
review.py's tested REST contract stays untouched — see PR-E notes in
README.md.
"""

import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.channels import whatsapp
from app.config import get_settings
from app.database import get_db
from app.engine import load_tactics
from app.llm import AnthropicSubagentClient
from app.models import AudienceEnum, Case, ChannelEnum, LLMCall, OutboundQueueItem, OutboundStatusEnum, Payment
from app.orchestrator import resume_after_escalation, status_message_for
from app.payments import (
    PreAuthRequiredError,
    cancel_for_walked_case,
    capture_for_won_case,
    handle_turn_outcome,
    require_pre_auth,
)

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_basic = HTTPBasic()
_ACTIONABLE_STATUSES = {OutboundStatusEnum.pending_approval, OutboundStatusEnum.edited}
VAULT_DIR = "vault"
THREAD_HISTORY_LIMIT = 10


def require_admin_auth(credentials: HTTPBasicCredentials = Depends(_basic)) -> str:
    expected = get_settings().review_token
    if not secrets.compare_digest(credentials.password, expected):
        raise HTTPException(status_code=401, detail="invalid credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


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


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)):
    items = (
        db.execute(
            select(OutboundQueueItem)
            .where(OutboundQueueItem.status.in_(_ACTIONABLE_STATUSES))
            .order_by(OutboundQueueItem.created_at)
        )
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        request, "dashboard.html", {"items": items, "operator": operator}
    )


@router.post("/queue/{msg_id}/approve")
async def approve(msg_id: uuid.UUID, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)):
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")
    if item.channel.value != "whatsapp":
        raise HTTPException(status_code=501, detail=f"sending for channel '{item.channel.value}' isn't wired up yet")
    if item.audience is AudienceEnum.counterparty:
        try:
            require_pre_auth(item.case, vault_dir=VAULT_DIR)
        except PreAuthRequiredError as exc:
            raise HTTPException(status_code=409, detail="payment pre-authorization required") from exc

    await whatsapp.send_text_message(item.recipient, item.message)

    now = datetime.now(timezone.utc)
    item.status = OutboundStatusEnum.sent
    item.sent_at = now
    item.reviewed_at = now
    item.reviewed_by = operator
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/queue/{msg_id}/edit")
def edit(
    msg_id: uuid.UUID,
    message: str = Form(...),
    operator: str = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    item.message = message
    item.status = OutboundStatusEnum.edited
    item.reviewed_at = datetime.now(timezone.utc)
    item.reviewed_by = operator
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/queue/{msg_id}/reject")
def reject(msg_id: uuid.UUID, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)):
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    item.status = OutboundStatusEnum.rejected
    item.reviewed_at = datetime.now(timezone.utc)
    item.reviewed_by = operator
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/cases", response_class=HTMLResponse)
def case_list(request: Request, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)):
    cases = db.execute(select(Case).order_by(Case.created_at.desc())).scalars().all()
    return templates.TemplateResponse(request, "cases.html", {"cases": cases, "operator": operator})


@router.get("/cases/{case_id}", response_class=HTMLResponse)
def case_detail(
    case_id: uuid.UUID, request: Request, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)
):
    case = _get_case(db, case_id)
    return templates.TemplateResponse(request, "case_detail.html", {"case": case, "operator": operator})


@router.post("/cases/{case_id}/answer")
def answer_escalation(
    case_id: uuid.UUID,
    answer: str = Form(...),
    operator: str = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    """Resume an ESCALATEd case with the operator's answer — the panel's view
    onto app.orchestrator.resume_after_escalation, same as
    POST /review/case/{id}/answer (app/review.py); see there for the
    queueing shape this mirrors."""
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
        case, client, answer, thread, tactics, vault_dir=VAULT_DIR, answered_by=operator
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
    return RedirectResponse(url=f"/admin/cases/{case_id}", status_code=303)


@router.get("/costs", response_class=HTMLResponse)
def costs(request: Request, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)):
    per_case = db.execute(
        select(
            LLMCall.case_id,
            func.count(LLMCall.id).label("calls"),
            func.sum(LLMCall.input_tokens).label("input_tokens"),
            func.sum(LLMCall.output_tokens).label("output_tokens"),
            func.avg(LLMCall.latency_ms).label("avg_latency_ms"),
        )
        .where(LLMCall.case_id.is_not(None))
        .group_by(LLMCall.case_id)
        .order_by(func.sum(LLMCall.input_tokens + LLMCall.output_tokens).desc())
    ).all()
    case_ids = [row.case_id for row in per_case]
    cases_by_id = {c.id: c for c in db.execute(select(Case).where(Case.id.in_(case_ids))).scalars().all()}

    per_role = db.execute(
        select(
            LLMCall.role,
            LLMCall.model,
            func.count(LLMCall.id).label("calls"),
            func.sum(LLMCall.input_tokens).label("input_tokens"),
            func.sum(LLMCall.output_tokens).label("output_tokens"),
            func.avg(LLMCall.latency_ms).label("avg_latency_ms"),
        )
        .group_by(LLMCall.role, LLMCall.model)
        .order_by(LLMCall.role)
    ).all()

    return templates.TemplateResponse(
        request,
        "costs.html",
        {
            "per_case": per_case,
            "cases_by_id": cases_by_id,
            "per_role": per_role,
            "operator": operator,
        },
    )


@router.get("/payments", response_class=HTMLResponse)
def payments_list(request: Request, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)):
    payments = db.execute(select(Payment).order_by(Payment.created_at.desc())).scalars().all()
    return templates.TemplateResponse(request, "payments.html", {"payments": payments, "operator": operator})


@router.post("/cases/{case_id}/payment/capture")
def payment_capture_override(
    case_id: uuid.UUID, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)
):
    """Manual operator override — for when the automatic capture_for_won_case
    hook (called right after run_turn/resume_after_escalation) missed a case,
    e.g. an outcome flip that happened outside a normal turn."""
    case = _get_case(db, case_id)
    payment = capture_for_won_case(case, vault_dir=VAULT_DIR)
    if payment is None:
        raise HTTPException(status_code=409, detail="nothing to capture (no pre-authorized payment)")
    db.commit()
    return RedirectResponse(url=f"/admin/cases/{case_id}", status_code=303)


@router.post("/cases/{case_id}/payment/cancel")
def payment_cancel_override(
    case_id: uuid.UUID, operator: str = Depends(require_admin_auth), db: Session = Depends(get_db)
):
    case = _get_case(db, case_id)
    payment = cancel_for_walked_case(case)
    if payment is None:
        raise HTTPException(status_code=409, detail="nothing to cancel (no pre-authorized payment)")
    db.commit()
    return RedirectResponse(url=f"/admin/cases/{case_id}", status_code=303)
