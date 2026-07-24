import json

from app.engine import load_tactics
from app.intake import run_intake_turn
from app.models import StateEnum
from app.subagents import SubagentRole

VAULT_DIR = "vault"


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


def _intake_response(reply, collected_fields, missing_fields, ready, memory_updates=None):
    return json.dumps(
        {
            "reply": reply,
            "collected_fields": collected_fields,
            "missing_fields": missing_fields,
            "ready": ready,
            "memory_updates": memory_updates or {},
        }
    )


def _stratejist_response(**overrides):
    payload = {
        "anchor": 88000,
        "target": 90000,
        "floor": 85000,
        "concession_ladder": [3000, 1500],
        "primary_tactics": ["TK-001"],
        "fallback_tactics": [],
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_run_intake_turn_missing_fields_asks_question(make_user):
    user = make_user()
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.intake: [
                _intake_response(
                    "Hangi bölgede oturuyorsunuz?",
                    {"mulk_adres": None, "hedef_kira": None, "ev_sahibi_iletisim": None},
                    ["hedef_kira", "ev_sahibi_iletisim"],
                    False,
                )
            ]
        }
    )

    result = run_intake_turn(user, client, "Merhaba, kiramı düşürmek istiyorum", [], tactics)

    assert result.status == "reply"
    assert result.reply == "Hangi bölgede oturuyorsunuz?"
    assert user.intake_state["ready"] is False
    assert user.intake_state["awaiting_confirmation"] is False
    assert user.intake_state["missing_fields"] == ["hedef_kira", "ev_sahibi_iletisim"]


def test_run_intake_turn_ready_sets_awaiting_confirmation_without_creating_case(make_user, db_session):
    user = make_user()
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.intake: [
                _intake_response(
                    "Özet: ... Onaylıyor musunuz?",
                    {
                        "mulk_adres": "Marina",
                        "hedef_kira": 90000,
                        "ev_sahibi_iletisim": "+9715000000",
                        "taban_kira": 85000,
                    },
                    [],
                    True,
                )
            ]
        }
    )

    result = run_intake_turn(user, client, "90 bine indirmek istiyorum", [], tactics)

    assert result.status == "reply"
    assert "Onaylıyor" in result.reply
    assert user.intake_state["ready"] is True
    assert user.intake_state["awaiting_confirmation"] is True
    assert result.case is None
    assert len(user.cases) == 0


def test_run_intake_turn_confirmation_creates_case_and_calls_stratejist(make_user):
    user = make_user()
    user.intake_state = {
        "collected_fields": {
            "mulk_adres": "Marina",
            "hedef_kira": 90000,
            "taban_kira": 85000,
            "tavan_kira": 100000,
            "ev_sahibi_iletisim": "+9715000000",
            "ev_sahibi_adi": "Ali",
        },
        "missing_fields": [],
        "ready": True,
        "awaiting_confirmation": True,
    }
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient({SubagentRole.stratejist: [_stratejist_response()]})

    result = run_intake_turn(user, client, "evet onaylıyorum", [], tactics)

    assert result.status == "case_created"
    case = result.case
    assert case is not None
    assert case.vertical == "kira-bae"
    assert case.state is StateEnum.anchoring
    assert case.target_price == 90000
    assert case.min_acceptable_price == 85000
    assert case.max_price == 100000
    assert case.counterparty_contact == "+9715000000"
    assert case.counterparty_name == "Ali"
    assert case.plan == json.loads(_stratejist_response())
    assert user.intake_state is None
    assert case in user.cases


def test_run_intake_turn_writes_memory_updates(make_user):
    user = make_user()
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.intake: [
                _intake_response(
                    "Tek seferde mi ödersiniz?",
                    {"hedef_kira": 90000},
                    ["ev_sahibi_iletisim"],
                    False,
                    memory_updates={"risk_toleransi": "dusuk"},
                )
            ]
        }
    )

    run_intake_turn(user, client, "Tek çek öderim ama risk almak istemem", [], tactics)

    memory = {m.key: m.value for m in user.memory}
    assert memory == {"risk_toleransi": "dusuk"}


def test_run_intake_turn_memory_update_overwrites_existing_key(make_user):
    user = make_user()
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.intake: [
                _intake_response(
                    "Anladım.",
                    {"hedef_kira": 90000},
                    ["ev_sahibi_iletisim"],
                    False,
                    memory_updates={"risk_toleransi": "yuksek"},
                )
            ]
        }
    )
    from app.models import UserMemory

    user.memory.append(UserMemory(key="risk_toleransi", value="dusuk"))

    run_intake_turn(user, client, "Aslında risk alabilirim", [], tactics)

    memory = {m.key: m.value for m in user.memory}
    assert memory == {"risk_toleransi": "yuksek"}
    assert len(user.memory) == 1


def test_run_intake_turn_escalates_on_bad_json(make_user):
    user = make_user()
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient({SubagentRole.intake: ["not json", "still not json"]})

    result = run_intake_turn(user, client, "merhaba", [], tactics)

    assert result.status == "escalated"
    assert user.intake_state is None


def test_run_intake_turn_stratejist_escalation_during_confirmation(make_user):
    user = make_user()
    user.intake_state = {
        "collected_fields": {"hedef_kira": 90000, "ev_sahibi_iletisim": "+9715000000"},
        "missing_fields": [],
        "ready": True,
        "awaiting_confirmation": True,
    }
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient({SubagentRole.stratejist: ["not json", "still not json"]})

    result = run_intake_turn(user, client, "evet", [], tactics)

    assert result.status == "escalated"


def test_run_intake_turn_non_confirmation_reply_continues_conversation(make_user):
    user = make_user()
    user.intake_state = {
        "collected_fields": {"hedef_kira": 90000},
        "missing_fields": ["ev_sahibi_iletisim"],
        "ready": True,
        "awaiting_confirmation": True,
    }
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.intake: [
                _intake_response(
                    "Anladım, hedefi 95000 olarak güncelledim. Ev sahibinin iletişim bilgisi?",
                    {"hedef_kira": 95000},
                    ["ev_sahibi_iletisim"],
                    False,
                )
            ]
        }
    )

    result = run_intake_turn(user, client, "Aslında 95 bin istiyorum", [], tactics)

    assert result.status == "reply"
    assert user.intake_state["collected_fields"]["hedef_kira"] == 95000
    assert user.intake_state["awaiting_confirmation"] is False
