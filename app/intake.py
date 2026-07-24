"""Intake conversation orchestration (draft): the 5th subagent, which
onboards a new customer over WhatsApp before any Case exists for them.

Flow (see app/prompts/intake.md for the full contract):
    Every message from a User with no active Case -> Intake(JSON)
    -> engine updates User.intake_state {collected_fields, missing_fields, ready}
    -> once ready=True, the subagent's own reply carries the fee-approval ask
    -> the NEXT message is checked with a deterministic keyword match (not
       the LLM) for confirmation -> Case created from collected_fields,
       Stratejist called once to seed Case.plan, case moved to `anchoring`.
"""

from dataclasses import dataclass

from app.engine import NegotiationEngine, Tactic
from app.models import Case, ChannelEnum, StateEnum, User, UserMemory
from app.subagents import SubagentClient, SubagentEscalated, SubagentRole, call_subagent_json
from app.vault import VaultReader

CONFIRMATION_WORDS = {
    "evet",
    "onaylıyorum",
    "onayliyorum",
    "onaylıyoruz",
    "tamam",
    "kabul",
    "kabul ediyorum",
    "olur",
    "yes",
    "confirm",
    "confirmed",
    "ok",
    "okay",
}


@dataclass
class IntakeResult:
    status: str  # "reply" | "case_created" | "escalated"
    reply: str | None = None
    case: Case | None = None
    escalation_reason: str | None = None


def _is_confirmation(text: str) -> bool:
    normalized = text.strip().lower()
    return any(word in normalized for word in CONFIRMATION_WORDS)


def _apply_memory_updates(user: User, updates: dict) -> None:
    existing = {m.key: m for m in user.memory}
    for key, value in updates.items():
        if key in existing:
            existing[key].value = value
        else:
            user.memory.append(UserMemory(key=key, value=value))


def _create_case_from_fields(user: User, fields: dict) -> Case:
    case = Case(
        channel=ChannelEnum.whatsapp,
        vertical="kira-bae",
        state=StateEnum.discovery,
        counterparty_name=fields.get("ev_sahibi_adi"),
        counterparty_contact=fields.get("ev_sahibi_iletisim") or "",
        item_description=fields.get("mulk_adres"),
        target_price=fields.get("hedef_kira"),
        min_acceptable_price=fields.get("taban_kira"),
        max_price=fields.get("tavan_kira"),
    )
    user.cases.append(case)
    return case


def _confirm_and_create_case(
    user: User, client: SubagentClient, tactics: list[Tactic], vault_dir: str = "vault"
) -> IntakeResult:
    fields = (user.intake_state or {}).get("collected_fields", {})
    case = _create_case_from_fields(user, fields)

    try:
        plan = call_subagent_json(
            client,
            SubagentRole.stratejist,
            {
                "CASE": {"vertical": case.vertical, "state": case.state.value, "floor": case.min_acceptable_price},
                "TACTICS": [t.taktik_id for t in tactics],
                "INTEL": {},
                "PROFILE": {},
                "VAULT": VaultReader(vault_dir).read_for_role(SubagentRole.stratejist.value).to_dict(),
            },
        )
    except SubagentEscalated as exc:
        return IntakeResult(status="escalated", escalation_reason=str(exc))

    case.plan = plan
    NegotiationEngine(case, tactics=tactics).start_anchor()
    user.intake_state = None

    reply = (
        "Teşekkürler! Vakanız açıldı, ev sahibiyle görüşmeye başlıyoruz. Gelişmeleri buradan "
        "paylaşacağız. / Thanks! Your case is open — we're starting the conversation with the "
        "landlord and will keep you posted here."
    )
    return IntakeResult(status="case_created", case=case, reply=reply)


def run_intake_turn(
    user: User,
    client: SubagentClient,
    incoming_message: str,
    thread: list[dict],
    tactics: list[Tactic],
    vault_dir: str = "vault",
) -> IntakeResult:
    """Run one intake turn for an inbound message from a User with no active Case."""
    state = user.intake_state or {}

    if state.get("awaiting_confirmation") and _is_confirmation(incoming_message):
        return _confirm_and_create_case(user, client, tactics, vault_dir)

    try:
        data = call_subagent_json(
            client,
            SubagentRole.intake,
            {
                "INCOMING": incoming_message,
                "THREAD": thread,
                "MEMORY": {m.key: m.value for m in user.memory},
                "COLLECTED_FIELDS": state.get("collected_fields", {}),
                "VAULT": VaultReader(vault_dir).read_for_role(SubagentRole.intake.value).to_dict(),
            },
        )
    except SubagentEscalated as exc:
        return IntakeResult(status="escalated", escalation_reason=str(exc))

    _apply_memory_updates(user, data.get("memory_updates", {}))

    ready = bool(data["ready"])
    user.intake_state = {
        "collected_fields": data["collected_fields"],
        "missing_fields": data["missing_fields"],
        "ready": ready,
        "awaiting_confirmation": ready,
    }

    return IntakeResult(status="reply", reply=data["reply"])
