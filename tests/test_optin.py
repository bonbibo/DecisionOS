from datetime import datetime, timedelta, timezone

import pytest

import app.channels.email as email_module
import app.channels.whatsapp as whatsapp_module
from app.channels.email import send_initial_contact_email
from app.channels.whatsapp import OptInRequiredError, _has_valid_opt_in, send_text_message
from app.models import ChannelEnum, DirectionEnum, Message, OptIn, OptInMethodEnum


def _inbound_whatsapp_message(sender: str, minutes_ago: int = 0) -> Message:
    msg = Message(
        channel=ChannelEnum.whatsapp,
        direction=DirectionEnum.inbound,
        content="merhaba",
        sender=sender,
    )
    if minutes_ago:
        msg.created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return msg


# --- _has_valid_opt_in ---


def test_has_valid_opt_in_false_with_no_messages(db_session):
    assert _has_valid_opt_in(db_session, "+9715000000") is False


def test_has_valid_opt_in_true_with_recent_inbound_message(db_session):
    msg = _inbound_whatsapp_message("+9715000000")
    db_session.add(msg)
    db_session.commit()

    assert _has_valid_opt_in(db_session, "+9715000000") is True


def test_has_valid_opt_in_false_when_message_older_than_24h(db_session):
    msg = Message(
        channel=ChannelEnum.whatsapp,
        direction=DirectionEnum.inbound,
        content="merhaba",
        sender="+9715000000",
    )
    db_session.add(msg)
    db_session.commit()
    db_session.execute(
        Message.__table__.update()
        .where(Message.id == msg.id)
        .values(created_at=datetime.now(timezone.utc) - timedelta(hours=25))
    )
    db_session.commit()

    assert _has_valid_opt_in(db_session, "+9715000000") is False


def test_has_valid_opt_in_false_for_outbound_message(db_session):
    msg = Message(
        channel=ChannelEnum.whatsapp, direction=DirectionEnum.outbound, content="hi", sender="+9715000000"
    )
    db_session.add(msg)
    db_session.commit()

    assert _has_valid_opt_in(db_session, "+9715000000") is False


def test_has_valid_opt_in_false_for_wrong_channel(db_session):
    msg = Message(channel=ChannelEnum.web, direction=DirectionEnum.inbound, content="hi", sender="+9715000000")
    db_session.add(msg)
    db_session.commit()

    assert _has_valid_opt_in(db_session, "+9715000000") is False


def test_has_valid_opt_in_scoped_to_recipient(db_session):
    msg = _inbound_whatsapp_message("+9715000000")
    db_session.add(msg)
    db_session.commit()

    assert _has_valid_opt_in(db_session, "+9715559999") is False


# --- send_text_message guard ---


@pytest.mark.asyncio
async def test_send_text_message_raises_without_opt_in(db_session):
    with pytest.raises(OptInRequiredError):
        await send_text_message("+9715000000", "merhaba", db_session)


@pytest.mark.asyncio
async def test_send_text_message_proceeds_with_opt_in(db_session, monkeypatch):
    db_session.add(_inbound_whatsapp_message("+9715000000"))
    db_session.commit()

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"messages": [{"id": "wamid.fake"}]}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            return FakeResponse()

    monkeypatch.setattr(whatsapp_module.httpx, "AsyncClient", lambda: FakeAsyncClient())

    result = await send_text_message("+9715000000", "merhaba", db_session)
    assert result == {"messages": [{"id": "wamid.fake"}]}


# --- send_initial_contact_email ---


def test_send_initial_contact_email_noop_without_email(new_case):
    new_case.counterparty_email = None
    assert send_initial_contact_email(new_case) is None


def test_send_initial_contact_email_sends_when_email_present(new_case, monkeypatch):
    new_case.counterparty_email = "landlord@example.com"
    new_case.counterparty_name = "Ali"

    calls = []
    monkeypatch.setattr(
        email_module, "send_email", lambda to, subject, body: calls.append((to, subject, body)) or {"id": "msg1"}
    )

    result = send_initial_contact_email(new_case)

    assert result == {"id": "msg1"}
    assert len(calls) == 1
    to, subject, body = calls[0]
    assert to == "landlord@example.com"
    assert "Ali" in body
    assert f"/optin/{new_case.id}" in body


# --- GET /optin/{case_id} ---


def test_optin_landing_404_for_unknown_case(api_client):
    import uuid

    resp = api_client.get(f"/optin/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_optin_landing_renders_and_records_opt_in(api_client, make_case, db_session):
    case = make_case(counterparty_contact="+9715000000", counterparty_name="Ali")

    resp = api_client.get(f"/optin/{case.id}")

    assert resp.status_code == 200
    assert "WhatsApp" in resp.text
    assert "wa.me" in resp.text

    opt_ins = db_session.query(OptIn).filter(OptIn.case_id == case.id).all()
    assert len(opt_ins) == 1
    assert opt_ins[0].method is OptInMethodEnum.email_link_click
    assert opt_ins[0].contact == "+9715000000"


# --- guard integration through /review and /admin approve() ---


def test_review_approve_409_without_opt_in(api_client, make_case, db_session):
    from app.config import get_settings
    from app.models import OutboundQueueItem, OutboundStatusEnum

    case = make_case(is_demo=True)  # exempt from payment guard, not opt-in guard
    item = OutboundQueueItem(
        case=case,
        channel=ChannelEnum.whatsapp,
        recipient="+15555550123",
        message="draft",
        status=OutboundStatusEnum.pending_approval,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    resp = api_client.post(
        f"/review/{item.id}/approve",
        json={},
        headers={"Authorization": f"Bearer {get_settings().review_token}"},
    )

    assert resp.status_code == 409
    assert "opt-in" in resp.json()["detail"]


def test_review_approve_succeeds_with_opt_in(api_client, make_case, db_session, monkeypatch):
    """Goes through the real send_text_message (only httpx is mocked) to
    prove the opt-in guard's positive path is actually wired end to end
    through POST /review/{id}/approve, not just unit-tested in isolation."""
    from app.config import get_settings
    from app.models import OutboundQueueItem, OutboundStatusEnum

    case = make_case(is_demo=True, counterparty_contact="+15555550123")
    db_session.add(_inbound_whatsapp_message("+15555550123"))
    item = OutboundQueueItem(
        case=case,
        channel=ChannelEnum.whatsapp,
        recipient="+15555550123",
        message="draft",
        status=OutboundStatusEnum.pending_approval,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"messages": [{"id": "wamid.fake"}]}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            return FakeResponse()

    monkeypatch.setattr(whatsapp_module.httpx, "AsyncClient", lambda: FakeAsyncClient())

    resp = api_client.post(
        f"/review/{item.id}/approve",
        json={},
        headers={"Authorization": f"Bearer {get_settings().review_token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"
