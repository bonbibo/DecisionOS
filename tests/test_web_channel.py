import base64
import json
import re

import app.channels.email as email_module
import app.channels.web as web_module
from app.config import get_settings
from app.models import (
    ActorEnum,
    AudienceEnum,
    Case,
    ChannelEnum,
    DirectionEnum,
    Message,
    MessageKindEnum,
    OutboundQueueItem,
    OutboundStatusEnum,
    StateEnum,
    User,
)
from app.subagents import SubagentRole


class ScriptedClient:
    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = {role: list(v) for role, v in responses.items()}
        self.calls: list[SubagentRole] = []

    def complete(self, role, system_prompt, payload):
        self.calls.append(role)
        queue = self._responses.get(role, [])
        assert queue, f"unexpected extra call to {role.value}"
        return queue.pop(0)


class ScriptedClientFactory:
    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = responses
        self.instances: list[ScriptedClient] = []

    def __call__(self, case_id, db, **kwargs):
        instance = ScriptedClient(self._responses)
        self.instances.append(instance)
        return instance


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


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register(api_client, monkeypatch, phone="+15550001111", email="a@b.com", name="Test User"):
    email_calls = []
    monkeypatch.setattr(
        email_module, "send_email", lambda to, subject, body: email_calls.append((to, subject, body))
    )

    resp = api_client.post("/web/auth/request-code", json={"email": email, "phone": phone, "name": name})
    assert resp.status_code == 200
    code = re.search(r"Giriş kodunuz: (\d{6})", email_calls[-1][2]).group(1)

    resp = api_client.post("/web/auth/verify-code", json={"email": email, "code": code})
    assert resp.status_code == 200
    return resp.json()


# --- /web/auth/request-code + /web/auth/verify-code ---


def test_request_verify_code_creates_user_with_session_token(api_client, db_session, monkeypatch):
    body = _register(api_client, monkeypatch)
    user = db_session.query(User).filter(User.phone == "+15550001111").one()
    assert str(user.id) == body["user_id"]
    assert user.web_session_token == body["session_token"]
    assert user.email == "a@b.com"
    assert user.name == "Test User"


def test_request_verify_code_existing_phone_reuses_user_and_reissues_token(api_client, db_session, make_user, monkeypatch):
    user = make_user(phone="+15550001111", email="old@b.com")
    old_token = user.web_session_token

    body = _register(api_client, monkeypatch, phone="+15550001111", email="new@b.com", name="Yeni İsim")

    db_session.refresh(user)
    assert body["user_id"] == str(user.id)
    assert user.email == "new@b.com"
    assert user.name == "Yeni İsim"
    assert user.web_session_token == body["session_token"]
    assert user.web_session_token != old_token
    assert db_session.query(User).count() == 1


# --- /web/chat auth ---


def test_chat_rejects_missing_bearer_token(api_client):
    resp = api_client.post("/web/chat", json={"message": "merhaba"})
    assert resp.status_code == 401


def test_chat_rejects_unknown_session_token(api_client):
    resp = api_client.post("/web/chat", json={"message": "merhaba"}, headers=_auth("nonexistent-token"))
    assert resp.status_code == 401


# --- /web/chat routing ---


def test_chat_no_active_case_routes_to_intake(api_client, db_session, monkeypatch):
    body = _register(api_client, monkeypatch)
    factory = ScriptedClientFactory({SubagentRole.intake: [_intake_question_response()]})
    monkeypatch.setattr(web_module, "AnthropicSubagentClient", factory)

    resp = api_client.post(
        "/web/chat", json={"message": "Merhaba, kiramı düşürmek istiyorum"}, headers=_auth(body["session_token"])
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["reply"] == "Hangi bölgede oturuyorsunuz?"
    assert payload["case_id"] is None

    messages = db_session.query(Message).all()
    assert len(messages) == 1
    assert messages[0].kind is MessageKindEnum.intake
    assert messages[0].case_id is None
    assert db_session.query(OutboundQueueItem).count() == 0  # synchronous, never queued


def test_chat_intake_confirmation_creates_case(api_client, db_session, make_user, monkeypatch):
    user = make_user(phone="+15550001111")
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
    user.web_session_token = "tok-confirm"
    db_session.commit()

    factory = ScriptedClientFactory({SubagentRole.stratejist: [_stratejist_response()]})
    monkeypatch.setattr(web_module, "AnthropicSubagentClient", factory)

    resp = api_client.post("/web/chat", json={"message": "evet onaylıyorum"}, headers=_auth("tok-confirm"))

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["case_id"] is not None
    assert payload["state"] == "anchoring"

    case = db_session.query(Case).filter(Case.counterparty_contact == "+9715000000").one()
    assert case.state is StateEnum.anchoring
    assert case.user_id == user.id
    db_session.refresh(user)
    assert user.intake_state is None


def test_chat_active_case_routes_to_negotiation(api_client, db_session, make_user, monkeypatch):
    user = make_user(phone="+15550001111")
    user.web_session_token = "tok-negotiate"
    case = Case(
        channel=ChannelEnum.web,
        vertical="kira-bae",
        counterparty_contact="+9715000000",
        counterparty_name="Ali",
        state=StateEnum.anchoring,
    )
    user.cases.append(case)
    db_session.commit()

    factory = ScriptedClientFactory(
        {
            SubagentRole.analist: [_analist_response()],
            SubagentRole.stratejist: [_stratejist_response()],
            SubagentRole.yazici: [_yazici_response()],
            SubagentRole.kritik: [_kritik_approve_response()],
        }
    )
    monkeypatch.setattr(web_module, "AnthropicSubagentClient", factory)

    resp = api_client.post("/web/chat", json={"message": "100000 istiyorum"}, headers=_auth("tok-negotiate"))

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["case_id"] == str(case.id)
    assert payload["escalated"] is False
    assert "reply" in payload and payload["reply"]

    items = db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).all()
    assert len(items) == 1  # only the counterparty draft is queued; client status is inline
    assert items[0].audience is AudienceEnum.counterparty
    assert items[0].channel.value == "whatsapp"
    assert items[0].recipient == "+9715000000"
    assert items[0].status is OutboundStatusEnum.pending_approval


def test_chat_negotiation_escalation_reflected_in_response(api_client, db_session, make_user, monkeypatch):
    user = make_user(phone="+15550001111")
    user.web_session_token = "tok-escalate"
    case = Case(
        channel=ChannelEnum.web,
        vertical="kira-bae",
        counterparty_contact="+9715000000",
        counterparty_name="Ali",
        state=StateEnum.anchoring,
    )
    user.cases.append(case)
    db_session.commit()

    factory = ScriptedClientFactory({SubagentRole.analist: ["not json", "still not json"]})
    monkeypatch.setattr(web_module, "AnthropicSubagentClient", factory)

    resp = api_client.post("/web/chat", json={"message": "??"}, headers=_auth("tok-escalate"))

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["escalated"] is True
    db_session.refresh(case)
    assert case.escalated is True
    assert db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).count() == 0


# --- /web/case/{id}/timeline ---


def test_timeline_returns_messages_and_offers_for_own_case(api_client, db_session, make_user):
    from app.engine import record_message, record_offer

    user = make_user(phone="+15550001111")
    user.web_session_token = "tok-timeline"
    case = Case(
        channel=ChannelEnum.web,
        counterparty_contact="+9715000000",
        state=StateEnum.anchoring,
    )
    user.cases.append(case)
    db_session.commit()

    record_message(case, channel=ChannelEnum.web, direction=DirectionEnum.inbound, content="merhaba", user=user)
    record_offer(case, actor=ActorEnum.us, price=90000, currency="AED")
    db_session.commit()

    resp = api_client.get(f"/web/case/{case.id}/timeline", headers=_auth("tok-timeline"))

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(case.id)
    assert body["state"] == "anchoring"
    assert len(body["messages"]) == 1
    assert body["messages"][0]["content"] == "merhaba"
    assert len(body["offers"]) == 1
    assert body["offers"][0]["price"] == 90000.0


def test_timeline_404_for_other_users_case(api_client, db_session, make_user):
    owner = make_user(phone="+15550001111")
    other = make_user(phone="+15550002222")
    other.web_session_token = "tok-other"
    case = Case(channel=ChannelEnum.web, counterparty_contact="+9715000000", state=StateEnum.anchoring)
    owner.cases.append(case)
    db_session.commit()

    resp = api_client.get(f"/web/case/{case.id}/timeline", headers=_auth("tok-other"))

    assert resp.status_code == 404


# --- /web/cases ---


def test_list_cases_requires_auth(api_client):
    resp = api_client.get("/web/cases")
    assert resp.status_code == 401


def test_list_cases_returns_only_own_cases_newest_first(api_client, db_session, make_user):
    owner = make_user(phone="+15550001111")
    owner.web_session_token = "tok-cases"
    other = make_user(phone="+15550002222")

    # Committed in separate transactions so Postgres's now() (same value for
    # every statement within one transaction) can't tie their created_at.
    older = Case(channel=ChannelEnum.web, counterparty_contact="+9715000000", state=StateEnum.anchoring)
    owner.cases.append(older)
    db_session.commit()

    newer = Case(channel=ChannelEnum.web, counterparty_contact="+9715000001", state=StateEnum.discovery)
    owner.cases.append(newer)
    db_session.commit()

    other.cases.append(Case(channel=ChannelEnum.web, counterparty_contact="+9715000002", state=StateEnum.discovery))
    db_session.commit()

    resp = api_client.get("/web/cases", headers=_auth("tok-cases"))

    assert resp.status_code == 200
    body = resp.json()
    assert [c["id"] for c in body] == [str(newer.id), str(older.id)]


# --- admin panel ---


def _basic_auth(password: str, username: str = "operator") -> dict:
    raw = f"{username}:{password}".encode()
    return {"Authorization": f"Basic {base64.b64encode(raw).decode()}"}


def test_admin_dashboard_requires_basic_auth(api_client):
    resp = api_client.get("/admin")
    assert resp.status_code == 401

    resp = api_client.get("/admin", headers=_basic_auth("wrong-token"))
    assert resp.status_code == 401


def test_admin_dashboard_lists_pending_items(api_client, make_case, db_session):
    case = make_case(counterparty_contact="+9715000000")
    item = OutboundQueueItem(
        case=case,
        channel=case.channel,
        recipient="+9715000000",
        message="draft message",
        status=OutboundStatusEnum.pending_approval,
    )
    db_session.add(item)
    db_session.commit()

    resp = api_client.get("/admin", headers=_basic_auth(get_settings().review_token))

    assert resp.status_code == 200
    assert "draft message" in resp.text


def test_admin_approve_sends_and_marks_sent(api_client, make_case, db_session, monkeypatch):
    import app.admin as admin_module

    # is_demo=True exempts the case from Package G's pre-auth guard (see
    # app.payments.require_pre_auth) — this test is about the send/mark-sent
    # mechanics, not payments.
    case = make_case(counterparty_contact="+9715000000", is_demo=True)
    item = OutboundQueueItem(
        case=case,
        channel=case.channel,
        recipient="+9715000000",
        message="draft message",
        status=OutboundStatusEnum.pending_approval,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    sent = []

    async def fake_send_text_message(to, body, db=None):
        sent.append((to, body))
        return {"messages": [{"id": "wamid.fake"}]}

    monkeypatch.setattr(admin_module.whatsapp, "send_text_message", fake_send_text_message)

    resp = api_client.post(
        f"/admin/queue/{item.id}/approve",
        headers=_basic_auth(get_settings().review_token),
        follow_redirects=False,
    )

    assert resp.status_code == 303
    db_session.refresh(item)
    assert item.status is OutboundStatusEnum.sent
    assert sent == [("+9715000000", "draft message")]


def test_admin_costs_page_renders(api_client):
    resp = api_client.get("/admin/costs", headers=_basic_auth(get_settings().review_token))
    assert resp.status_code == 200
