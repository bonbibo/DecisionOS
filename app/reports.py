"""Daily operations report (draft — Package J, extended by Package K).

Pure aggregation over existing tables — no new event log. One deliberate
approximation, documented where it's computed: "escalated cases" counts
Case rows with a non-null escalation_context whose updated_at falls in the
window, since there's no dedicated escalation-event table (Case.updated_at
moves on any field change, so this can over/undercount slightly).

Package K adds `phone_request_escalations`: the count within that same
window whose `escalation_category == phone_request` — this is the exact
numerator KR-003 (`vault/06-Kararlar/KR-003-ses-kanali-esigi.md`) measures
against total escalations to decide whether voice-channel investment is
justified. The report doesn't make that call; it just makes the ratio
visible.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Case, EscalationCategoryEnum, LLMCall, OutcomeEnum, Payment, PaymentStatusEnum, WaitlistSignup


@dataclass
class DailyReport:
    day: date
    new_cases: int
    closed_won: int
    closed_walked: int
    escalated_cases: int
    phone_request_escalations: int
    llm_calls: int
    llm_input_tokens: int
    llm_output_tokens: int
    captured_total: float
    new_waitlist_signups: int


def compute_daily_report(db: Session, day: date | None = None) -> DailyReport:
    day = day or (datetime.now(timezone.utc).date() - timedelta(days=1))
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    new_cases = db.execute(
        select(func.count(Case.id)).where(Case.created_at >= start, Case.created_at < end)
    ).scalar_one()

    closed_won = db.execute(
        select(func.count(Case.id)).where(
            Case.closed_at >= start, Case.closed_at < end, Case.outcome == OutcomeEnum.won
        )
    ).scalar_one()
    closed_walked = db.execute(
        select(func.count(Case.id)).where(
            Case.closed_at >= start, Case.closed_at < end, Case.outcome == OutcomeEnum.walked
        )
    ).scalar_one()

    escalated_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.escalation_context.is_not(None), Case.updated_at >= start, Case.updated_at < end
        )
    ).scalar_one()

    phone_request_escalations = db.execute(
        select(func.count(Case.id)).where(
            Case.escalation_category == EscalationCategoryEnum.phone_request,
            Case.updated_at >= start,
            Case.updated_at < end,
        )
    ).scalar_one()

    llm_calls, llm_input_tokens, llm_output_tokens = db.execute(
        select(
            func.count(LLMCall.id),
            func.coalesce(func.sum(LLMCall.input_tokens), 0),
            func.coalesce(func.sum(LLMCall.output_tokens), 0),
        ).where(LLMCall.created_at >= start, LLMCall.created_at < end)
    ).one()

    captured_total = db.execute(
        select(func.coalesce(func.sum(Payment.captured_amount), 0)).where(
            Payment.status == PaymentStatusEnum.captured, Payment.captured_at >= start, Payment.captured_at < end
        )
    ).scalar_one()

    new_waitlist_signups = db.execute(
        select(func.count(WaitlistSignup.id)).where(
            WaitlistSignup.created_at >= start, WaitlistSignup.created_at < end
        )
    ).scalar_one()

    return DailyReport(
        day=day,
        new_cases=new_cases,
        closed_won=closed_won,
        closed_walked=closed_walked,
        escalated_cases=escalated_cases,
        phone_request_escalations=phone_request_escalations,
        llm_calls=llm_calls,
        llm_input_tokens=llm_input_tokens,
        llm_output_tokens=llm_output_tokens,
        captured_total=float(captured_total),
        new_waitlist_signups=new_waitlist_signups,
    )


def render_daily_report(report: DailyReport) -> str:
    phone_request_ratio = (
        f"%{report.phone_request_escalations / report.escalated_cases * 100:.0f}"
        if report.escalated_cases
        else "—"
    )
    lines = [
        f"# Günlük Rapor — {report.day.isoformat()}",
        "",
        "| Metrik | Değer |",
        "|---|---|",
        f"| Yeni vaka | {report.new_cases} |",
        f"| Kapanan (kazanıldı) | {report.closed_won} |",
        f"| Kapanan (vazgeçildi) | {report.closed_walked} |",
        f"| Eskale olan vaka | {report.escalated_cases} |",
        f"| Telefon talebi eskalasyonu | {report.phone_request_escalations} ({phone_request_ratio}) |",
        f"| LLM çağrısı | {report.llm_calls} |",
        f"| LLM girdi token | {report.llm_input_tokens} |",
        f"| LLM çıktı token | {report.llm_output_tokens} |",
        f"| Tahsil edilen toplam | {report.captured_total:.2f} |",
        f"| Yeni waitlist kaydı | {report.new_waitlist_signups} |",
        "",
    ]
    return "\n".join(lines)
