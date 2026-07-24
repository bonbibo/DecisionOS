import json

import app.channels.whatsapp as whatsapp_module
import app.review as review_module
from app.models import ChannelEnum, OutboundQueueItem, OutboundStatusEnum
from app.subagents import SubagentRole

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
    return json.dumps({"message": "hello from the agent", "tactic_used": tactic_used})


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


def test_webhook_verification_handshake(api_client):
    resp = api_client.get(
        "/channels/whatsapp/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "change-me", "hub.challenge": "12345"},
    )
    assert resp.status_code == 200
    assert resp.text == "12345"


def test_webhook_approved_draft_lands_in_outbound_queue(api_client, make_case, db_session, monkeypatch):
    case = make_case(counterparty_contact="+15555550123")
    factory = ScriptedClientFactory(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)

    resp = api_client.post(
        "/channels/whatsapp/webhook", json=_whatsapp_payload("+15555550123", "merhaba, ilgileniyorum")
    )

    assert resp.status_code == 200
    items = (
        db_session.query(OutboundQueueItem)
        .filter(OutboundQueueItem.case_id == case.id)
        .all()
    )
    assert len(items) == 1
    assert items[0].status is OutboundStatusEnum.pending_approval
    assert items[0].message == "hello from the agent"
    assert items[0].channel is ChannelEnum.whatsapp
    assert items[0].recipient == "+15555550123"


def test_webhook_unknown_sender_is_dropped_without_crashing(api_client, db_session, caplog):
    resp = api_client.post(
        "/channels/whatsapp/webhook", json=_whatsapp_payload("+19998887777", "hello?")
    )

    assert resp.status_code == 200
    assert db_session.query(OutboundQueueItem).count() == 0
    assert "unknown sender" in caplog.text.lower()


def test_webhook_escalation_sets_case_flag_without_queueing(api_client, make_case, db_session, monkeypatch):
    case = make_case(counterparty_contact="+15555550123")
    factory = ScriptedClientFactory({SubagentRole.analist: ["not json", "still not json"]})
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)

    resp = api_client.post(
        "/channels/whatsapp/webhook", json=_whatsapp_payload("+15555550123", "merhaba")
    )

    assert resp.status_code == 200
    db_session.refresh(case)
    assert case.escalated is True
    assert db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).count() == 0


def test_review_approve_sends_and_marks_sent(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    item = OutboundQueueItem(
        case=case,
        channel=ChannelEnum.whatsapp,
        recipient="+15555550123",
        message="draft message",
        tactic_used="TK-001",
        status=OutboundStatusEnum.pending_approval,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    sent_calls = []

    async def fake_send_text_message(to, body):
        sent_calls.append((to, body))
        return {"messages": [{"id": "wamid.fake"}]}

    monkeypatch.setattr(review_module.whatsapp, "send_text_message", fake_send_text_message)

    resp = api_client.post(f"/review/{item.id}/approve", json={"reviewed_by": "gokhan"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "sent"
    assert body["sent_at"] is not None
    assert sent_calls == [("+15555550123", "draft message")]


def test_review_edit_updates_message_without_sending(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    item = OutboundQueueItem(
        case=case,
        channel=ChannelEnum.whatsapp,
        recipient="+15555550123",
        message="draft message",
        status=OutboundStatusEnum.pending_approval,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    sent_calls = []
    monkeypatch.setattr(
        review_module.whatsapp,
        "send_text_message",
        lambda to, body: sent_calls.append((to, body)),
    )

    resp = api_client.post(f"/review/{item.id}/edit", json={"message": "edited message"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "edited"
    assert body["message"] == "edited message"
    assert sent_calls == []


def test_review_reject_marks_rejected_without_sending(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    item = OutboundQueueItem(
        case=case,
        channel=ChannelEnum.whatsapp,
        recipient="+15555550123",
        message="draft message",
        status=OutboundStatusEnum.pending_approval,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    sent_calls = []
    monkeypatch.setattr(
        review_module.whatsapp,
        "send_text_message",
        lambda to, body: sent_calls.append((to, body)),
    )

    resp = api_client.post(f"/review/{item.id}/reject", json={})

    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert sent_calls == []


def test_review_approve_conflicts_once_already_sent(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    item = OutboundQueueItem(
        case=case,
        channel=ChannelEnum.whatsapp,
        recipient="+15555550123",
        message="draft message",
        status=OutboundStatusEnum.sent,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    resp = api_client.post(f"/review/{item.id}/approve", json={})
    assert resp.status_code == 409


def test_review_approve_404_for_unknown_id(api_client):
    import uuid

    resp = api_client.post(f"/review/{uuid.uuid4()}/approve", json={})
    assert resp.status_code == 404
