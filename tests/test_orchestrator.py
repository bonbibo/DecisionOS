import json
from pathlib import Path

from app.engine import load_tactics
from app.models import StateEnum
from app.orchestrator import run_turn
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

    def complete(self, role, system_prompt, payload):
        self.calls.append(role)
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
