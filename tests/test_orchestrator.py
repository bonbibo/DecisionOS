import json
from pathlib import Path

from app.engine import load_tactics
from app.models import ActorEnum, OutcomeEnum, StateEnum
from app.orchestrator import resume_after_escalation, run_turn
from app.subagents import SubagentRole

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"

ANALIST_OK = json.dumps({"archetype": "A2", "recommended_state": "anchoring"})
STRATEJIST_OK = json.dumps(
    {
        "anchor": 90000,
        "target": 95000,
        "floor": 85000,
        "concession_ladder": [4000, 2000, 1000],
        "primary_tactics": ["TK-001", "TK-003"],
        "fallback_tactics": ["TK-002"],
    }
)


def _yazici(tactic_used="TK-001"):
    return json.dumps({"message": "hello", "tactic_used": tactic_used})


def _kritik(verdict, **extra):
    return json.dumps({"verdict": verdict, **extra})


class ScriptedClient:
    """Fake SubagentClient: a queue of raw responses per role, popped in order."""

    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = {role: list(v) for role, v in responses.items()}
        self.calls: list[SubagentRole] = []
        self.payloads: dict[SubagentRole, list[dict]] = {}

    def complete(self, role, system_prompt, payload):
        self.calls.append(role)
        self.payloads.setdefault(role, []).append(payload)
        queue = self._responses.get(role, [])
        assert queue, f"unexpected extra call to {role.value}"
        return queue.pop(0)


def test_run_turn_approves_on_first_pass(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "approved"
    assert result.draft["message"] == "hello"
    assert new_case.state is StateEnum.anchoring
    assert new_case.plan == json.loads(STRATEJIST_OK)
    assert new_case.escalated is False
    assert new_case.escalation_reason is None


def test_run_turn_reuses_existing_plan_without_recalling_stratejist(new_case):
    new_case.vertical = "kira-bae"
    new_case.plan = json.loads(STRATEJIST_OK)
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "approved"
    assert SubagentRole.stratejist not in client.calls


def test_run_turn_revise_loop_then_approve(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici(), _yazici()],
            SubagentRole.kritik: [_kritik("REVISE", revision_note="be shorter"), _kritik("APPROVE")],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "approved"
    assert client.calls.count(SubagentRole.yazici) == 2
    assert client.calls.count(SubagentRole.kritik) == 2


def test_run_turn_max_revisions_exceeded_escalates(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    # MAX_REVISIONS = 2 -> 3 Yazıcı/Kritik attempts allowed, all REVISE.
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici(), _yazici(), _yazici()],
            SubagentRole.kritik: [
                _kritik("REVISE", revision_note="a"),
                _kritik("REVISE", revision_note="b"),
                _kritik("REVISE", revision_note="c"),
            ],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "escalated"
    assert new_case.escalated is True
    assert "revision" in new_case.escalation_reason


def test_run_turn_reject_triggers_replan_then_approves(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK, STRATEJIST_OK],
            SubagentRole.yazici: [_yazici(), _yazici()],
            SubagentRole.kritik: [_kritik("REJECT"), _kritik("APPROVE")],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "approved"
    assert client.calls.count(SubagentRole.stratejist) == 2


def test_run_turn_reject_after_max_replans_escalates(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    # MAX_REJECT_REPLANS = 1 -> 2 planning rounds allowed, both REJECT.
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK, STRATEJIST_OK],
            SubagentRole.yazici: [_yazici(), _yazici()],
            SubagentRole.kritik: [_kritik("REJECT"), _kritik("REJECT")],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "escalated"
    assert new_case.escalated is True


def test_run_turn_kritik_escalate_stops_immediately(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("ESCALATE", violations=["7: telefon istedi"])],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "escalated"
    assert new_case.escalated is True
    assert "telefon" in new_case.escalation_reason
    assert client.calls.count(SubagentRole.yazici) == 1


def test_run_turn_analist_escalation_short_circuits(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: ["not json", "still not json"],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "escalated"
    assert new_case.escalated is True
    assert new_case.state is StateEnum.discovery  # unchanged
    assert SubagentRole.stratejist not in client.calls


def test_run_turn_escalation_records_incoming_message_in_context(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient({SubagentRole.analist: ["not json", "still not json"]})

    run_turn(new_case, client, "100000 istiyorum", thread=[], tactics=tactics)

    assert new_case.escalation_context["incoming_message"] == "100000 istiyorum"


def test_run_turn_passes_human_guidance_to_every_subagent(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics, human_guidance="telefon isteği normal, onayla")

    for role in (SubagentRole.analist, SubagentRole.stratejist, SubagentRole.yazici, SubagentRole.kritik):
        assert client.payloads[role][0]["HUMAN_GUIDANCE"] == "telefon isteği normal, onayla"


def test_resume_after_escalation_reuses_stored_incoming_message_and_appends_answer(new_case):
    new_case.vertical = "kira-bae"
    new_case.escalated = True
    new_case.escalation_reason = "7: telefon istedi"
    new_case.escalation_context = {"incoming_message": "telefon numaramı verir misin diyor"}
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    result = resume_after_escalation(
        new_case, client, "Bu normal, telefon numarasını paylaşabilirsin", thread=[], tactics=tactics,
        answered_by="gokhan",
    )

    assert result.status == "approved"
    assert new_case.escalated is False
    assert client.payloads[SubagentRole.analist][0]["INCOMING"] == "telefon numaramı verir misin diyor"
    assert client.payloads[SubagentRole.kritik][0]["HUMAN_GUIDANCE"] == "Bu normal, telefon numarasını paylaşabilirsin"

    answers = new_case.escalation_context["human_answers"]
    assert len(answers) == 1
    assert answers[0]["answer"] == "Bu normal, telefon numarasını paylaşabilirsin"
    assert answers[0]["answered_by"] == "gokhan"
    assert answers[0]["answered_at"]


def test_resume_after_escalation_can_re_escalate_and_still_appends_answer(new_case):
    new_case.vertical = "kira-bae"
    new_case.escalated = True
    new_case.escalation_context = {"incoming_message": "merhaba"}
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient({SubagentRole.analist: ["not json", "still not json"]})

    result = resume_after_escalation(new_case, client, "bak bakalım", thread=[], tactics=tactics)

    assert result.status == "escalated"
    assert new_case.escalated is True
    assert len(new_case.escalation_context["human_answers"]) == 1
    assert new_case.escalation_context["incoming_message"] == "merhaba"


def test_run_turn_illegal_recommended_state_escalates(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    # discovery -> counter skips anchoring; not a legal transition.
    client = ScriptedClient(
        {
            SubagentRole.analist: [json.dumps({"archetype": "A2", "recommended_state": "counter"})],
        }
    )

    result = run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert result.status == "escalated"
    assert new_case.state is StateEnum.discovery
    assert new_case.escalated is True


def test_run_turn_includes_vault_block_for_every_subagent_call(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics, vault_dir=str(VAULT_DIR))

    for role in (SubagentRole.analist, SubagentRole.stratejist, SubagentRole.yazici, SubagentRole.kritik):
        payload = client.payloads[role][0]
        assert "VAULT" in payload
        assert "documents" in payload["VAULT"]
        assert "warnings" in payload["VAULT"]

    # yazici's manifest entry is scoped to taktikler/ only, not the whole playbook.
    yazici_paths = {d["path"] for d in client.payloads[SubagentRole.yazici][0]["VAULT"]["documents"]}
    assert yazici_paths == {
        "01-Playbooks/taktikler/TK-001-rakip-teklif.md",
        "01-Playbooks/taktikler/TK-002-kosul-takasi.md",
        "01-Playbooks/taktikler/TK-003-sessizlik-deadline.md",
        "01-Playbooks/taktikler/TK-101-paralel-bayi.md",
        "01-Playbooks/taktikler/TK-102-otd-ayristirma.md",
        "01-Playbooks/taktikler/TK-103-ay-sonu.md",
        "01-Playbooks/taktikler/TK-201-nakit-bugun.md",
        "01-Playbooks/taktikler/TK-202-kusur-gerekce.md",
    }


def test_apply_recommended_state_close_sets_outcome_won(new_case):
    new_case.vertical = "kira-bae"
    new_case.state = StateEnum.counter
    new_case.plan = json.loads(STRATEJIST_OK)  # skip Stratejist — not the point of this test
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [json.dumps({"archetype": "A2", "recommended_state": "close"})],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "anlastik", thread=[], tactics=tactics)

    assert new_case.outcome is OutcomeEnum.won
    assert new_case.state is StateEnum.close


def test_apply_recommended_state_walk_sets_outcome_walked(new_case):
    new_case.vertical = "kira-bae"
    new_case.state = StateEnum.counter
    new_case.plan = json.loads(STRATEJIST_OK)  # skip Stratejist — not the point of this test
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [json.dumps({"archetype": "A2", "recommended_state": "walk"})],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "vazgeciyorum", thread=[], tactics=tactics)

    assert new_case.outcome is OutcomeEnum.walked
    assert new_case.state is StateEnum.close


def test_apply_recommended_state_other_states_leave_outcome_none(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert new_case.outcome is None


def test_run_turn_records_counterparty_offer_from_analist(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [json.dumps({"archetype": "A2", "recommended_state": "anchoring", "counter_offer": 105000})],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "105000 istiyorum", thread=[], tactics=tactics)

    offers = [o for o in new_case.offers if o.actor == ActorEnum.counterparty]
    assert len(offers) == 1
    assert offers[0].price == 105000


def test_run_turn_records_our_offer_from_approved_draft(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hello", "tactic_used": "TK-001", "offer_made": 92000})],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    offers = [o for o in new_case.offers if o.actor == ActorEnum.us]
    assert len(offers) == 1
    assert offers[0].price == 92000


def test_run_turn_no_offer_recorded_when_offer_fields_absent_or_null(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert new_case.offers == []
