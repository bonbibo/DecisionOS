"""Turn orchestration (draft).

Wires the subagent flow described in app/prompts/README.md for one incoming
message:

    Analist(JSON) -> state update
    -> (Stratejist, only at case open or after a REJECT verdict)
    -> Yazıcı(draft JSON) <-> Kritik(verdict)
         APPROVE  -> return the draft for the human-in-the-loop send queue
         REVISE   -> back to Yazıcı with a revision_note (max MAX_REVISIONS)
         REJECT   -> re-run Stratejist (max MAX_REJECT_REPLANS), then retry
         ESCALATE -> stop immediately, hand off to a human

A bad/unparseable subagent response already escalates inside
app.subagents.call_subagent_json (one retry, then SubagentEscalated); this
module handles the higher-level APPROVE/REVISE/REJECT/ESCALATE branching on
top of that.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.engine import InvalidTransition, NegotiationEngine, Tactic
from app.models import Case, StateEnum
from app.subagents import SubagentClient, SubagentEscalated, SubagentRole, Verdict, call_subagent_json
from app.vault import VaultReader

MAX_REVISIONS = 2
MAX_REJECT_REPLANS = 1


def _vault_block(role: SubagentRole, vault_dir: str = "vault") -> dict:
    """Everything vault/_manifest.md assigns `role`, ready to embed in its payload."""
    context = VaultReader(vault_dir).read_for_role(role.value)
    return context.exclude_inactive_decisions().to_dict()


def _get_segment(case: Case) -> str | None:
    """The case's own customer segment (S1/S2/S3, from vault/08-Musteri-Profilleri/segmentler.md
    via UserMemory) — None if the case has no linked user or the segment isn't known yet."""
    if not case.user:
        return None
    return next((m.value for m in case.user.memory if m.key == "segment"), None)


@dataclass
class TurnResult:
    status: str  # "approved" | "escalated"
    draft: dict | None = None
    analysis: dict | None = None
    plan: dict | None = None
    escalation_reason: str | None = None


def _apply_recommended_state(engine: NegotiationEngine, recommended_state: str) -> None:
    target = StateEnum.close if recommended_state == "walk" else StateEnum(recommended_state)
    if target is engine.case.state:
        return
    engine.transition(target)


def _select_tactic(plan: dict, tactics: list[Tactic]) -> Tactic | None:
    candidate_ids = [*plan.get("primary_tactics", []), *plan.get("fallback_tactics", [])]
    by_id = {t.taktik_id: t for t in tactics}
    for taktik_id in candidate_ids:
        if taktik_id in by_id:
            return by_id[taktik_id]
    return None


def _draft_and_review(
    client: SubagentClient,
    case: Case,
    plan: dict,
    tactic: Tactic | None,
    thread: list[dict],
    analysis: dict,
    vault_dir: str = "vault",
    human_guidance: str | None = None,
) -> TurnResult:
    """Run the Yazıcı <-> Kritik loop for one plan. Returns status "approved",
    "rejected" (caller should re-plan), or "escalated"."""
    revision_note = None
    for _ in range(MAX_REVISIONS + 1):
        try:
            draft = call_subagent_json(
                client,
                SubagentRole.yazici,
                {
                    "PLAN": plan,
                    "STATE": {"asama": case.state.value},
                    "TACTIC": tactic.body if tactic else None,
                    "THREAD": thread,
                    "ANALYSIS": analysis,
                    "REVISION_NOTE": revision_note,
                    "VAULT": _vault_block(SubagentRole.yazici, vault_dir),
                    "HUMAN_GUIDANCE": human_guidance,
                },
            )
        except SubagentEscalated as exc:
            return TurnResult(status="escalated", analysis=analysis, plan=plan, escalation_reason=str(exc))

        try:
            verdict_data = call_subagent_json(
                client,
                SubagentRole.kritik,
                {
                    "DRAFT": draft,
                    "TACTIC": tactic.body if tactic else None,
                    "PLAN": plan,
                    "VAULT": _vault_block(SubagentRole.kritik, vault_dir),
                    "HUMAN_GUIDANCE": human_guidance,
                },
            )
        except SubagentEscalated as exc:
            return TurnResult(
                status="escalated", analysis=analysis, plan=plan, draft=draft, escalation_reason=str(exc)
            )

        try:
            verdict = Verdict(verdict_data["verdict"])
        except ValueError as exc:
            return TurnResult(
                status="escalated", analysis=analysis, plan=plan, draft=draft, escalation_reason=str(exc)
            )
        if verdict is Verdict.approve:
            return TurnResult(status="approved", draft=draft, analysis=analysis, plan=plan)
        if verdict is Verdict.escalate:
            reason = "; ".join(verdict_data.get("violations", [])) or "kritik escalate"
            return TurnResult(
                status="escalated", analysis=analysis, plan=plan, draft=draft, escalation_reason=reason
            )
        if verdict is Verdict.reject:
            return TurnResult(status="rejected", analysis=analysis, plan=plan, draft=draft)
        # REVISE: loop again with Kritik's correction note.
        revision_note = verdict_data.get("revision_note")

    return TurnResult(
        status="escalated", analysis=analysis, plan=plan, escalation_reason="max revisions exceeded"
    )


def run_turn(
    case: Case,
    client: SubagentClient,
    incoming_message: str,
    thread: list[dict],
    tactics: list[Tactic],
    profiles: list[dict] | None = None,
    intel: dict | None = None,
    vault_dir: str = "vault",
    human_guidance: str | None = None,
) -> TurnResult:
    """Run one negotiation turn for an incoming counterparty message.

    Mutates `case` in place (state, plan, escalated/escalation_reason) the
    same way NegotiationEngine does elsewhere; callers persist it via a
    DB session. `human_guidance` is only set when resuming a previously
    ESCALATEd case with an operator's answer (see resume_after_escalation) —
    it rides alongside every subagent call so Analist/Stratejist/Yazıcı/Kritik
    can factor it in; it's None on a normal turn.
    """
    engine = NegotiationEngine(case, tactics=tactics)

    try:
        analysis = call_subagent_json(
            client,
            SubagentRole.analist,
            {
                "INCOMING": incoming_message,
                "THREAD": thread,
                "PROFILES": profiles or [],
                "STATE": {"asama": case.state.value},
                "VAULT": _vault_block(SubagentRole.analist, vault_dir),
                "HUMAN_GUIDANCE": human_guidance,
            },
        )
    except SubagentEscalated as exc:
        return _escalate(case, TurnResult(status="escalated", escalation_reason=str(exc)), incoming_message)

    try:
        _apply_recommended_state(engine, analysis["recommended_state"])
    except (ValueError, InvalidTransition) as exc:
        return _escalate(
            case, TurnResult(status="escalated", analysis=analysis, escalation_reason=str(exc)), incoming_message
        )

    plan = case.plan
    result = None
    for _ in range(MAX_REJECT_REPLANS + 1):
        if plan is None:
            try:
                plan = call_subagent_json(
                    client,
                    SubagentRole.stratejist,
                    {
                        "CASE": {
                            "vertical": case.vertical,
                            "state": case.state.value,
                            "floor": case.min_acceptable_price,
                        },
                        "TACTICS": [t.taktik_id for t in tactics],
                        "INTEL": intel or {},
                        "PROFILE": analysis,
                        "SEGMENT": _get_segment(case),
                        "VAULT": _vault_block(SubagentRole.stratejist, vault_dir),
                        "HUMAN_GUIDANCE": human_guidance,
                    },
                )
            except SubagentEscalated as exc:
                return _escalate(
                    case,
                    TurnResult(status="escalated", analysis=analysis, escalation_reason=str(exc)),
                    incoming_message,
                )
            case.plan = plan

        tactic = _select_tactic(plan, tactics)
        result = _draft_and_review(client, case, plan, tactic, thread, analysis, vault_dir, human_guidance)

        if result.status != "rejected":
            break
        plan = None  # force a fresh Stratejist plan on the next loop
    else:
        result = TurnResult(
            status="escalated", analysis=analysis, plan=plan, escalation_reason="reject after max replans"
        )

    if result.status == "escalated":
        return _escalate(case, result, incoming_message)
    case.escalated = False
    case.escalation_reason = None
    return result


def _escalate(case: Case, result: TurnResult, incoming_message: str | None = None) -> TurnResult:
    case.escalated = True
    case.escalation_reason = result.escalation_reason
    if incoming_message is not None:
        context = dict(case.escalation_context or {})
        context["incoming_message"] = incoming_message
        case.escalation_context = context
    return result


def resume_after_escalation(
    case: Case,
    client: SubagentClient,
    human_answer: str,
    thread: list[dict],
    tactics: list[Tactic],
    profiles: list[dict] | None = None,
    intel: dict | None = None,
    vault_dir: str = "vault",
    answered_by: str | None = None,
) -> TurnResult:
    """Re-run the turn that triggered an ESCALATE, now with an operator's
    answer attached as HUMAN_GUIDANCE. Requires `case.escalated` — callers
    (POST /review/case/{id}/answer, the admin panel) are responsible for
    that check and for queueing an approved draft afterwards, same as
    run_turn(). The original incoming message is read back from
    `case.escalation_context` (set by _escalate); every answer is appended
    there too, so the full Q&A trail is on the Case as a dataset artifact
    in its own right, alongside the raw LLM I/O in LLMCall.
    """
    context = dict(case.escalation_context or {})
    incoming_message = context.get("incoming_message", "")
    answers = list(context.get("human_answers", []))
    answers.append(
        {
            "answer": human_answer,
            "answered_by": answered_by,
            "answered_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    context["human_answers"] = answers
    case.escalation_context = context

    return run_turn(
        case,
        client,
        incoming_message,
        thread,
        tactics,
        profiles=profiles,
        intel=intel,
        vault_dir=vault_dir,
        human_guidance=human_answer,
    )


def status_message_for(result: TurnResult, case: Case) -> str:
    """A short client-facing status update for one run_turn() result — shown to
    our own customer (not the counterparty), either queued (WhatsApp) or
    returned inline (web). See app.channels.whatsapp and app.channels.web."""
    if result.status == "escalated":
        return (
            "Görüşmede bir noktayı ekibimize danışıyoruz, kısa süre içinde güncelleme geleceğiz. / "
            "We're checking one detail with our team on your negotiation — an update is coming shortly."
        )
    return (
        f"Görüşme devam ediyor ({case.state.value}). Yeni gelişme oldu, onayınızı bekliyoruz. / "
        f"Negotiation in progress ({case.state.value}). There's a new development awaiting your review."
    )
