import hashlib
import hmac
import json
import uuid

import app.channels.whatsapp as whatsapp_module
import app.review as review_module
from app.config import get_settings
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


def _signature(body: bytes) -> str:
    secret = get_settings().whatsapp_app_secret
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post_webhook(api_client, payload: dict, *, signature: str | None = "__valid__"):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if signature == "__valid__":
        headers["X-Hub-Signature-256"] = _signature(body)
    elif signature is not None:
        headers["X-Hub-Signature-256"] = signature
    return api_client.post("/channels/whatsapp/webhook", content=body, headers=headers)


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {get_settings().review_token}"}


def test_webhook_verification_handshake(api_client):
    resp = api_client.get(
        "/channels/whatsapp/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "change-me", "hub.challenge": "12345"},
    )
    assert resp.status_code == 200
    assert resp.text == "12345"


def test_webhook_rejects_missing_signature(api_client, make_case):
    make_case(counterparty_contact="+15555550123")

    resp = _post_webhook(
        api_client, _whatsapp_payload("+15555550123", "merhaba"), signature=None
    )

    assert resp.status_code == 401


def test_webhook_rejects_invalid_signature(api_client, make_case):
    make_case(counterparty_contact="+15555550123")

    resp = _post_webhook(
        api_client, _whatsapp_payload("+15555550123", "merhaba"), signature="sha256=deadbeef"
    )

    assert resp.status_code == 401


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

    resp = _post_webhook(api_client, _whatsapp_payload("+15555550123", "merhaba, ilgileniyorum"))

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


def test_webhook_escalation_sets_case_flag_without_queueing(api_client, make_case, db_session, monkeypatch):
    case = make_case(counterparty_contact="+15555550123")
    factory = ScriptedClientFactory({SubagentRole.analist: ["not json", "still not json"]})
    monkeypatch.setattr(whatsapp_module, "AnthropicSubagentClient", factory)

    resp = _post_webhook(api_client, _whatsapp_payload("+15555550123", "merhaba"))

    assert resp.status_code == 200
    db_session.refresh(case)
    assert case.escalated is True
    assert db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).count() == 0


def test_review_endpoints_require_bearer_token(api_client, make_case, db_session):
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

    no_header = api_client.post(f"/review/{item.id}/approve", json={})
    assert no_header.status_code == 401

    wrong_token = api_client.post(
        f"/review/{item.id}/approve", json={}, headers={"Authorization": "Bearer wrong-token"}
    )
    assert wrong_token.status_code == 401


def test_review_approve_sends_and_marks_sent(api_client, make_case, db_session, monkeypatch):
    # is_demo=True exempts the case from Package G's pre-auth guard (see
    # app.payments.require_pre_auth) — this test is about the send/mark-sent
    # mechanics, not payments.
    case = make_case(is_demo=True)
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

    async def fake_send_text_message(to, body, db=None):
        sent_calls.append((to, body))
        return {"messages": [{"id": "wamid.fake"}]}

    monkeypatch.setattr(review_module.whatsapp, "send_text_message", fake_send_text_message)

    resp = api_client.post(
        f"/review/{item.id}/approve", json={"reviewed_by": "gokhan"}, headers=_auth_headers()
    )

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

    resp = api_client.post(
        f"/review/{item.id}/edit", json={"message": "edited message"}, headers=_auth_headers()
    )

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

    resp = api_client.post(f"/review/{item.id}/reject", json={}, headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert sent_calls == []


def test_review_approve_conflicts_once_already_sent(api_client, make_case, db_session):
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

    resp = api_client.post(f"/review/{item.id}/approve", json={}, headers=_auth_headers())
    assert resp.status_code == 409


def test_review_approve_404_for_unknown_id(api_client):
    resp = api_client.post(f"/review/{uuid.uuid4()}/approve", json={}, headers=_auth_headers())
    assert resp.status_code == 404
