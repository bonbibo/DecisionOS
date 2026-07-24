import base64

from app.config import get_settings
from app.models import WaitlistSignup


def _basic_auth(password: str, username: str = "operator") -> dict:
    raw = f"{username}:{password}".encode()
    return {"Authorization": f"Basic {base64.b64encode(raw).decode()}"}


def test_landing_page_renders(api_client):
    resp = api_client.get("/")
    assert resp.status_code == 200
    assert "waitlist" in resp.text.lower() or "Bekleme listesine" in resp.text


def test_join_waitlist_creates_signup(api_client, db_session):
    resp = api_client.post("/waitlist", json={"email": "a@b.com", "phone": "+15551234", "note": "acil"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "a@b.com"

    signup = db_session.query(WaitlistSignup).filter(WaitlistSignup.email == "a@b.com").one()
    assert signup.phone == "+15551234"
    assert signup.note == "acil"


def test_join_waitlist_resubmit_updates_not_duplicates(api_client, db_session):
    api_client.post("/waitlist", json={"email": "a@b.com", "note": "ilk"})
    api_client.post("/waitlist", json={"email": "a@b.com", "note": "ikinci", "phone": "+15559999"})

    signups = db_session.query(WaitlistSignup).filter(WaitlistSignup.email == "a@b.com").all()
    assert len(signups) == 1
    assert signups[0].note == "ikinci"
    assert signups[0].phone == "+15559999"


def test_join_waitlist_requires_email(api_client):
    resp = api_client.post("/waitlist", json={"phone": "+15551234"})
    assert resp.status_code == 422


def test_waitlist_thanks_page_renders(api_client):
    resp = api_client.get("/waitlist/thanks")
    assert resp.status_code == 200


def test_admin_waitlist_requires_auth(api_client):
    resp = api_client.get("/admin/waitlist")
    assert resp.status_code == 401


def test_admin_waitlist_lists_signups(api_client, db_session):
    db_session.add(WaitlistSignup(email="a@b.com", phone="+15551234"))
    db_session.commit()

    resp = api_client.get("/admin/waitlist", headers=_basic_auth(get_settings().review_token))

    assert resp.status_code == 200
    assert "a@b.com" in resp.text
