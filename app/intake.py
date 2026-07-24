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

from app.config import get_settings
from app.engine import NegotiationEngine, Tactic
from app.models import Case, ChannelEnum, StateEnum, User, UserMemory
from app.payments import checkout_link, create_pre_auth
from app.subagents import SubagentClient, SubagentEscalated, SubagentRole, call_subagent_json
from app.vault import VaultReader

INTAKE_VERTICAL = "kira-bae"
MAX_FEE_REVISIONS = 1


def _vault_block(role: SubagentRole, vault_dir: str = "vault") -> dict:
    """Everything vault/_manifest.md assigns `role`, ready to embed in its payload."""
    context = VaultReader(vault_dir).read_for_role(role.value)
    return context.exclude_inactive_decisions().to_dict()


def _get_intel(case: Case, vault_dir: str = "vault") -> dict:
    """Mirrors app.orchestrator._get_intel — auto-populated market intel for
    the case's vertical (vault/09-Piyasa-Verisi/<dikey>.md), {} if none/not aktif."""
    if not case.vertical:
        return {}
    context = VaultReader(vault_dir).read_folder("09-Piyasa-Verisi", recursive=False)
    for doc in context.documents:
        frontmatter = doc.frontmatter or {}
        if frontmatter.get("dikey") == case.vertical and frontmatter.get("durum") == "aktif":
            return frontmatter
    return {}

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


def _select_pricing(vault_documents: list[dict], dikey: str, allow_demo: bool = False) -> dict | None:
    """Find the vault/07-Fiyatlama/<dikey>.md frontmatter for a vertical.

    Only `durum: aktif` pricing is offered to real customers; `demo` entries
    (e.g. arac-bae while it's unvalidated) require `allow_demo=True` — which
    intake never passes, since intake only ever opens real (non-demo) cases.
    """
    allowed_statuses = {"aktif"} | ({"demo"} if allow_demo else set())
    for doc in vault_documents:
        frontmatter = doc.get("frontmatter") or {}
        if (
            frontmatter.get("dikey") == dikey
            and frontmatter.get("durum") in allowed_statuses
            and "fiyat_id" in frontmatter
        ):
            return frontmatter
    return None


def _fee_mismatch(fee_offer: dict | None, pricing: dict) -> str | None:
    """None if `fee_offer` matches `pricing`'s numbers; otherwise a correction note for the subagent."""
    if not fee_offer:
        return "fee_offer is missing but ready=true; fill it in from PRICING"

    expected = {
        "basari_yuzdesi": pricing.get("basari_yuzdesi"),
        "min_ucret": pricing.get("min_ucret"),
        "para_birimi": pricing.get("para_birimi"),
    }
    actual = {key: fee_offer.get(key) for key in expected}
    if actual != expected:
        return f"fee_offer {actual} does not match PRICING {expected} — use PRICING's numbers exactly"
    return None


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
        vertical=INTAKE_VERTICAL,
        state=StateEnum.discovery,
        counterparty_name=fields.get("ev_sahibi_adi"),
        counterparty_contact=fields.get("ev_sahibi_iletisim") or "",
        counterparty_email=fields.get("ev_sahibi_email"),
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
    stratejist_vault = _vault_block(SubagentRole.stratejist, vault_dir)

    try:
        plan = call_subagent_json(
            client,
            SubagentRole.stratejist,
            {
                "CASE": {"vertical": case.vertical, "state": case.state.value, "floor": case.min_acceptable_price},
                "TACTICS": [t.taktik_id for t in tactics],
                "INTEL": _get_intel(case, vault_dir),
                "PROFILE": {},
                "SEGMENT": next((m.value for m in user.memory if m.key == "segment"), None),
                "VAULT": stratejist_vault,
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

    # Card pre-authorization (Package G) — only for priced, non-demo verticals;
    # `create_pre_auth` just attaches Payment via the case.payment relationship,
    # no db access needed here (caller persists case + its cascaded children).
    pricing = _select_pricing(stratejist_vault["documents"], case.vertical) if case.vertical else None
    if pricing is not None:
        payment = create_pre_auth(case, pricing)
        link = checkout_link(payment, get_settings().public_base_url)
        reply += (
            f" Devam etmeden önce kartınızı doğrulamanız gerekiyor (ücret SADECE kazandırırsak, kapanışta "
            f"tahsil edilir): {link} / Before we continue, please verify a card (you're only charged if "
            f"we actually save you money, at closing): {link}"
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

    vault_context = _vault_block(SubagentRole.intake, vault_dir)
    pricing = _select_pricing(vault_context["documents"], INTAKE_VERTICAL)

    revision_note = None
    data = None
    for attempt in range(MAX_FEE_REVISIONS + 1):
        try:
            data = call_subagent_json(
                client,
                SubagentRole.intake,
                {
                    "INCOMING": incoming_message,
                    "THREAD": thread,
                    "MEMORY": {m.key: m.value for m in user.memory},
                    "COLLECTED_FIELDS": state.get("collected_fields", {}),
                    "PRICING": pricing,
                    "REVISION_NOTE": revision_note,
                    "VAULT": vault_context,
                },
            )
        except SubagentEscalated as exc:
            return IntakeResult(status="escalated", escalation_reason=str(exc))

        if not data["ready"] or pricing is None:
            break

        mismatch = _fee_mismatch(data.get("fee_offer"), pricing)
        if mismatch is None:
            break
        if attempt >= MAX_FEE_REVISIONS:
            return IntakeResult(status="escalated", escalation_reason=f"fee validation failed: {mismatch}")
        revision_note = mismatch

    _apply_memory_updates(user, data.get("memory_updates", {}))

    ready = bool(data["ready"])
    user.intake_state = {
        "collected_fields": data["collected_fields"],
        "missing_fields": data["missing_fields"],
        "ready": ready,
        "awaiting_confirmation": ready,
    }

    return IntakeResult(status="reply", reply=data["reply"])
