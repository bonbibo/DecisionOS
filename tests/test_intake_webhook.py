import hashlib
import hmac
import json

import app.channels.whatsapp as whatsapp_module
from app.config import get_settings
from app.models import (
    AudienceEnum,
    Case,
    Message,
    MessageKindEnum,
    OutboundQueueItem,
    OutboundStatusEnum,
    StateEnum,
    User,
)
from app.subagents import SubagentRole


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


class ScriptedClientFactory:
    """Drop-in replacement for AnthropicSubagentClient's constructor signature."""

    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = responses
        self.instances: list[ScriptedClient] = []

    def __call__(self, case_id, db, **kwargs):
        instance = ScriptedClient(self._responses)
        self.instances.append(instance)
        return instance


def _whatsapp_payload(sender: str, text: str) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {"value": {"messages": [{"from": sender, "type": "text", "text": {"body": text}}]}}
                ]
            }
        ]
    }


def _signature(body: bytes) -> str:
    secret = get_settings().whatsapp_app_secret
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post_webhook(api_client, payload: dict):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "X-Hub-Signature-256": _signature(body)}
    return api_client.post("/channels/whatsapp/webhook", content=body, headers=headers)


def _fake_send(monkeypatch):
    sent = []

    async def fake_send_text_message(to, body, db=None):
        sent.append((to, body))
        return {"messages": [{"id": "wamid.fake"}]}

    monkeypatch.setattr(whatsapp_module, "send_text_message", fake_send_text_message)
    return sent


def _intake_question_response():
    return json.dumps(
        {
            "reply": "Hangi bölgede oturuyorsunuz?",
            "collected_fields": {},
            "missing_fields": ["hedef_kira", "ev_sahibi_iletisim"],
            "ready": False,
            "memory_updates": {},
        }
    )


def _stratejist_response():
    return json.dumps(
        {
            "anchor": 88000,
            "target": 90000,
            "floor": 85000,
            "concession_ladder": [3000, 1500],
            "primary_tactics": ["TK-001"],
            "fallback_tactics": [],
        }
    )


def _analist_response():
    return json.dumps({"archetype": "A2", "recommended_state": "anchoring"})


def _yazici_response():
    return json.dumps({"message": "hello", "tactic_used": "TK-001"})


def _kritik_approve_response():
    return json.dumps({"verdict": "APPROVE"})


def test_webhook_new_sender_creates_user_and_sends_reply_directly(api_client, db_session, monkeypatch):
    factory = ScriptedClientFactory({SubagentRole.intake: [_intake_question_response()]})
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)
    sent = _fake_send(monkeypatch)

    resp = _post_webhook(
        api_client, _whatsapp_payload("+19998887777", "Merhaba, kiramı düşürmek istiyorum")
    )

    assert resp.status_code == 200
    user = db_session.query(User).filter(User.phone == "+19998887777").one()
    assert user.intake_state["ready"] is False
    assert sent == [("+19998887777", "Hangi bölgede oturuyorsunuz?")]
    assert db_session.query(OutboundQueueItem).count() == 0  # direct send, not queued


def test_webhook_intake_message_persisted_as_kind_intake_with_no_case(api_client, db_session, monkeypatch):
    factory = ScriptedClientFactory({SubagentRole.intake: [_intake_question_response()]})
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)
    _fake_send(monkeypatch)

    _post_webhook(api_client, _whatsapp_payload("+19998887777", "Merhaba"))

    messages = db_session.query(Message).all()
    assert len(messages) == 1
    assert messages[0].kind is MessageKindEnum.intake
    assert messages[0].case_id is None
    assert messages[0].user_id is not None


def test_webhook_intake_confirmation_creates_case_and_sends_confirmation_directly(
    api_client, db_session, make_user, monkeypatch
):
    user = make_user(phone="+19998887777")
    user.intake_state = {
        "collected_fields": {
            "hedef_kira": 90000,
            "ev_sahibi_iletisim": "+9715000000",
            "mulk_adres": "Marina",
        },
        "missing_fields": [],
        "ready": True,
        "awaiting_confirmation": True,
    }
    db_session.commit()

    factory = ScriptedClientFactory({SubagentRole.stratejist: [_stratejist_response()]})
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)
    sent = _fake_send(monkeypatch)

    resp = _post_webhook(api_client, _whatsapp_payload("+19998887777", "evet onaylıyorum"))

    assert resp.status_code == 200
    case = db_session.query(Case).filter(Case.counterparty_contact == "+9715000000").one()
    assert case.state is StateEnum.anchoring
    assert case.user_id == user.id
    assert len(sent) == 1
    assert sent[0][0] == "+19998887777"
    db_session.refresh(user)
    assert user.intake_state is None


def test_webhook_active_case_routes_to_negotiation_not_intake(api_client, make_case, db_session, monkeypatch):
    make_case(counterparty_contact="+15555550123")
    factory = ScriptedClientFactory(
        {
            SubagentRole.analist: [_analist_response()],
            SubagentRole.stratejist: [_stratejist_response()],
            SubagentRole.yazici: [_yazici_response()],
            SubagentRole.kritik: [_kritik_approve_response()],
        }
    )
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)

    resp = _post_webhook(api_client, _whatsapp_payload("+15555550123", "100000 istiyorum"))

    assert resp.status_code == 200
    assert db_session.query(User).count() == 0  # negotiation path never touches User/intake


def test_webhook_negotiation_queues_client_status_update_when_case_has_user(
    api_client, make_case, make_user, db_session, monkeypatch
):
    user = make_user(phone="+19998887777")
    case = make_case(counterparty_contact="+15555550123", user=user)
    factory = ScriptedClientFactory(
        {
            SubagentRole.analist: [_analist_response()],
            SubagentRole.stratejist: [_stratejist_response()],
            SubagentRole.yazici: [_yazici_response()],
            SubagentRole.kritik: [_kritik_approve_response()],
        }
    )
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)

    resp = _post_webhook(api_client, _whatsapp_payload("+15555550123", "100000 istiyorum"))

    assert resp.status_code == 200
    items = db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).all()
    audiences = {item.audience for item in items}
    assert audiences == {AudienceEnum.counterparty, AudienceEnum.client}
    client_item = next(i for i in items if i.audience is AudienceEnum.client)
    assert client_item.recipient == "+19998887777"
    assert client_item.status is OutboundStatusEnum.pending_approval
