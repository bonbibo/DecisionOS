import json
from pathlib import Path

from app.engine import load_tactics
from app.intake import _fee_mismatch, _select_pricing, run_intake_turn
from app.subagents import SubagentRole
from app.vault import VaultReader

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"

KIRA_BAE_FEE_OFFER = {"basari_yuzdesi": 25, "min_ucret": 500, "para_birimi": "AED"}
ARAC_BAE_FEE_OFFER = {"basari_yuzdesi": 20, "min_ucret": 400, "para_birimi": "AED"}


class ScriptedClient:
    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = {role: list(v) for role, v in responses.items()}
        self.calls: list[SubagentRole] = []

    def complete(self, role, system_prompt, payload):
        self.calls.append(role)
        queue = self._responses.get(role, [])
        assert queue, f"unexpected extra call to {role.value}"
        return queue.pop(0)


def _fiyatlama_docs() -> list[dict]:
    return VaultReader(VAULT_DIR).read_folder("07-Fiyatlama", recursive=False).to_dict()["documents"]


def _intake_ready_response(fee_offer):
    return json.dumps(
        {
            "reply": "Özet ... Onaylıyor musunuz?",
            "collected_fields": {"hedef_kira": 90000, "ev_sahibi_iletisim": "+9715000000"},
            "missing_fields": [],
            "ready": True,
            "memory_updates": {},
            "fee_offer": fee_offer,
        }
    )


def test_select_pricing_returns_correct_dikey():
    docs = _fiyatlama_docs()
    pricing = _select_pricing(docs, "kira-bae")
    assert pricing["fiyat_id"] == "FY-kira-bae"
    assert pricing["basari_yuzdesi"] == 25


def test_select_pricing_excludes_demo_by_default():
    docs = _fiyatlama_docs()
    assert _select_pricing(docs, "arac-bae") is None


def test_select_pricing_allows_demo_when_requested():
    docs = _fiyatlama_docs()
    pricing = _select_pricing(docs, "arac-bae", allow_demo=True)
    assert pricing["fiyat_id"] == "FY-arac-bae"
    assert pricing["durum"] == "demo"


def test_select_pricing_missing_dikey_returns_none():
    docs = _fiyatlama_docs()
    assert _select_pricing(docs, "saglik-bae") is None


def test_fee_mismatch_none_when_numbers_match():
    docs = _fiyatlama_docs()
    pricing = _select_pricing(docs, "kira-bae")
    assert _fee_mismatch(KIRA_BAE_FEE_OFFER, pricing) is None


def test_fee_mismatch_flags_wrong_percentage():
    docs = _fiyatlama_docs()
    pricing = _select_pricing(docs, "kira-bae")
    wrong = {**KIRA_BAE_FEE_OFFER, "basari_yuzdesi": 30}
    assert _fee_mismatch(wrong, pricing) is not None


def test_fee_mismatch_flags_missing_fee_offer():
    docs = _fiyatlama_docs()
    pricing = _select_pricing(docs, "kira-bae")
    assert _fee_mismatch(None, pricing) is not None


def test_run_intake_turn_wrong_fee_offer_triggers_one_revision_then_succeeds(make_user):
    user = make_user()
    tactics = load_tactics(VAULT_DIR)
    wrong_fee = {"basari_yuzdesi": 30, "min_ucret": 500, "para_birimi": "AED"}
    client = ScriptedClient(
        {
            SubagentRole.intake: [
                _intake_ready_response(wrong_fee),
                _intake_ready_response(KIRA_BAE_FEE_OFFER),
            ]
        }
    )

    result = run_intake_turn(user, client, "90 bine indirmek istiyorum", [], tactics, vault_dir=str(VAULT_DIR))

    assert result.status == "reply"
    assert client.calls == [SubagentRole.intake, SubagentRole.intake]
    assert user.intake_state["awaiting_confirmation"] is True


def test_run_intake_turn_persistent_fee_mismatch_escalates(make_user):
    user = make_user()
    tactics = load_tactics(VAULT_DIR)
    wrong_fee = {"basari_yuzdesi": 30, "min_ucret": 500, "para_birimi": "AED"}
    client = ScriptedClient(
        {
            SubagentRole.intake: [
                _intake_ready_response(wrong_fee),
                _intake_ready_response(wrong_fee),
            ]
        }
    )

    result = run_intake_turn(user, client, "90 bine indirmek istiyorum", [], tactics, vault_dir=str(VAULT_DIR))

    assert result.status == "escalated"
    assert "fee validation failed" in result.escalation_reason
    assert client.calls == [SubagentRole.intake, SubagentRole.intake]
