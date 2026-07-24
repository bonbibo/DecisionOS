import json
from pathlib import Path

from app.engine import load_tactics
from app.intake import run_intake_turn
from app.models import ChannelEnum, StateEnum, User, UserMemory
from app.orchestrator import run_turn
from app.subagents import SubagentRole
from app.vault import VaultReader

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"

ANALIST_OK = json.dumps({"archetype": "A2", "recommended_state": "anchoring"})
STRATEJIST_OK = json.dumps(
    {
        "anchor": 90000,
        "target": 95000,
        "floor": 85000,
        "concession_ladder": [4000, 2000, 1000],
        "primary_tactics": ["TK-001"],
        "fallback_tactics": [],
    }
)


class RecordingClient:
    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = {role: list(v) for role, v in responses.items()}
        self.payloads: dict[SubagentRole, list[dict]] = {}

    def complete(self, role, system_prompt, payload):
        self.payloads.setdefault(role, []).append(payload)
        return self._responses[role].pop(0)


def test_run_turn_stratejist_gets_segment_from_case_user_memory(new_case):
    new_case.vertical = "kira-bae"
    user = User(phone="+15555550199")
    user.memory.append(UserMemory(key="segment", value="S1"))
    new_case.user = user

    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=[])

    payload = client.payloads[SubagentRole.stratejist][0]
    assert payload["SEGMENT"] == "S1"


def test_run_turn_stratejist_segment_none_without_user(new_case):
    new_case.vertical = "kira-bae"
    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=[])

    payload = client.payloads[SubagentRole.stratejist][0]
    assert payload["SEGMENT"] is None


def test_run_turn_stratejist_segment_none_when_user_has_no_segment_memory(new_case):
    new_case.vertical = "kira-bae"
    user = User(phone="+15555550199")
    user.memory.append(UserMemory(key="risk_toleransi", value="dusuk"))
    new_case.user = user

    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=[])

    payload = client.payloads[SubagentRole.stratejist][0]
    assert payload["SEGMENT"] is None


def test_intake_confirmation_passes_segment_to_stratejist(make_user):
    user = make_user()
    user.memory.append(UserMemory(key="segment", value="S3"))
    user.intake_state = {
        "collected_fields": {"hedef_kira": 90000, "ev_sahibi_iletisim": "+9715000000"},
        "missing_fields": [],
        "ready": True,
        "awaiting_confirmation": True,
    }
    tactics = load_tactics(VAULT_DIR)
    client = RecordingClient({SubagentRole.stratejist: [STRATEJIST_OK]})

    run_intake_turn(user, client, "evet", [], tactics, vault_dir=str(VAULT_DIR))

    payload = client.payloads[SubagentRole.stratejist][0]
    assert payload["SEGMENT"] == "S3"


def test_read_for_role_analist_includes_customer_segments():
    ctx = VaultReader(VAULT_DIR).read_for_role("analist")
    segment_doc = next(d for d in ctx.documents if d.path == "08-Musteri-Profilleri/segmentler.md")
    assert "S1" in segment_doc.body
    assert "S2" in segment_doc.body
    assert "S3" in segment_doc.body
