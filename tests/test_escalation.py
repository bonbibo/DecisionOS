"""Human-in-the-loop question/answer flow: an ESCALATEd Case gets resumed via
POST /review/case/{id}/answer (REST) or the /admin panel's equivalent form."""

import base64
import json

import app.review as review_module
from app.config import get_settings
from app.models import AudienceEnum, ChannelEnum, OutboundQueueItem, OutboundStatusEnum, StateEnum
from app.subagents import SubagentRole

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

    def __call__(self, case_id, db, **kwargs):
        return ScriptedClient(self._responses)


def _yazici():
    return json.dumps({"message": "hello", "tactic_used": "TK-001"})


def _kritik(verdict, **extra):
    return json.dumps({"verdict": verdict, **extra})


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {get_settings().review_token}"}


def _basic_auth(password: str, username: str = "operator") -> dict:
    raw = f"{username}:{password}".encode()
    return {"Authorization": f"Basic {base64.b64encode(raw).decode()}"}


def _escalated_case(make_case, **overrides):
    defaults = dict(
        escalated=True,
        escalation_reason="7: telefon istedi",
        escalation_context={"incoming_message": "telefon numaramı verir misin diyor"},
    )
    defaults.update(overrides)
    return make_case(**defaults)


# --- POST /review/case/{id}/answer ---


def test_answer_requires_bearer_token(api_client, make_case):
    case = _escalated_case(make_case)
    resp = api_client.post(f"/review/case/{case.id}/answer", json={"answer": "devam et"})
    assert resp.status_code == 401


def test_answer_404_for_unknown_case(api_client):
    import uuid

    resp = api_client.post(
        f"/review/case/{uuid.uuid4()}/answer", json={"answer": "devam et"}, headers=_auth_headers()
    )
    assert resp.status_code == 404


def test_answer_409_when_case_not_escalated(api_client, make_case):
    case = make_case()
    resp = api_client.post(f"/review/case/{case.id}/answer", json={"answer": "devam et"}, headers=_auth_headers())
    assert resp.status_code == 409


def test_answer_resumes_and_queues_counterparty_draft(api_client, make_case, db_session, monkeypatch):
    case = _escalated_case(make_case)
    factory = ScriptedClientFactory(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )
    monkeypatch.setattr(review_module, "AnthropicSubagentClient", factory)

    resp = api_client.post(
        f"/review/case/{case.id}/answer",
        json={"answer": "Bu normal, paylaşabilirsin", "reviewed_by": "gokhan"},
        headers=_auth_headers(),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["escalated"] is False

    db_session.refresh(case)
    assert case.escalated is False
    assert case.escalation_context["human_answers"][0]["answered_by"] == "gokhan"

    items = db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).all()
    assert len(items) == 1
    assert items[0].audience is AudienceEnum.counterparty
    assert items[0].channel is ChannelEnum.whatsapp
    assert items[0].status is OutboundStatusEnum.pending_approval


def test_answer_queues_client_status_update_when_case_has_user(api_client, make_case, make_user, db_session, monkeypatch):
    user = make_user(phone="+19998887777")
    case = _escalated_case(make_case, user=user)
    factory = ScriptedClientFactory(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )
    monkeypatch.setattr(review_module, "AnthropicSubagentClient", factory)

    api_client.post(
        f"/review/case/{case.id}/answer", json={"answer": "devam et"}, headers=_auth_headers()
    )

    items = db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).all()
    audiences = {i.audience for i in items}
    assert audiences == {AudienceEnum.counterparty, AudienceEnum.client}
    client_item = next(i for i in items if i.audience is AudienceEnum.client)
    assert client_item.recipient == "+19998887777"


def test_answer_still_escalated_only_queues_client_status(api_client, make_case, make_user, db_session, monkeypatch):
    user = make_user(phone="+19998887777")
    case = _escalated_case(make_case, user=user)
    factory = ScriptedClientFactory({SubagentRole.analist: ["not json", "still not json"]})
    monkeypatch.setattr(review_module, "AnthropicSubagentClient", factory)

    resp = api_client.post(
        f"/review/case/{case.id}/answer", json={"answer": "tekrar dene"}, headers=_auth_headers()
    )

    assert resp.status_code == 200
    assert resp.json()["escalated"] is True
    items = db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).all()
    assert len(items) == 1
    assert items[0].audience is AudienceEnum.client


# --- /admin/cases/{id}/answer ---


def test_admin_answer_requires_basic_auth(api_client, make_case):
    case = _escalated_case(make_case)
    resp = api_client.post(f"/admin/cases/{case.id}/answer", data={"answer": "devam et"})
    assert resp.status_code == 401


def test_admin_answer_resumes_case_and_redirects(api_client, make_case, db_session, monkeypatch):
    import app.admin as admin_module

    case = _escalated_case(make_case)
    factory = ScriptedClientFactory(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("APPROVE")],
        }
    )
    monkeypatch.setattr(admin_module, "AnthropicSubagentClient", factory)

    resp = api_client.post(
        f"/admin/cases/{case.id}/answer",
        data={"answer": "onayla ve devam et"},
        headers=_basic_auth(get_settings().review_token),
        follow_redirects=False,
    )

    assert resp.status_code == 303
    assert resp.headers["location"] == f"/admin/cases/{case.id}"

    db_session.refresh(case)
    assert case.escalated is False
    assert case.state is StateEnum.anchoring
    assert db_session.query(OutboundQueueItem).filter(OutboundQueueItem.case_id == case.id).count() == 1


def test_admin_answer_409_when_not_escalated(api_client, make_case):
    case = make_case()
    resp = api_client.post(
        f"/admin/cases/{case.id}/answer",
        data={"answer": "devam et"},
        headers=_basic_auth(get_settings().review_token),
    )
    assert resp.status_code == 409


def test_admin_case_detail_shows_answer_form_when_escalated(api_client, make_case):
    case = _escalated_case(make_case)
    resp = api_client.get(f"/admin/cases/{case.id}", headers=_basic_auth(get_settings().review_token))
    assert resp.status_code == 200
    assert "Soruyu Yanıtla" in resp.text
    assert "telefon istedi" in resp.text
