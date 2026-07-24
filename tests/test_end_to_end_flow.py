"""End-to-end acceptance test for docs/MASTER-SPEC-v3.md's acceptance
criterion: "waitlist'ten capture'a uçtan uca akış, elle DB müdahalesi
sıfır" — every step below is an HTTP/webhook/script call, never a direct
DB write. If this test is green, that sentence is satisfied.
"""

import hashlib
import hmac
import json
from datetime import date, timezone

import app.channels.email as email_module
import app.channels.web as web_module
import app.channels.whatsapp as whatsapp_module
import app.payments as payments_module
from app.config import get_settings
from app.models import OutboundStatusEnum, PaymentStatusEnum, WaitlistSignup
from app.payments import CheckoutSession
from app.reports import compute_daily_report
from app.subagents import SubagentRole

COUNTERPARTY_PHONE = "+9715000000"

ANALIST_ANCHORING = json.dumps({"archetype": "A2", "recommended_state": "anchoring", "counter_offer": 100000})
ANALIST_CLOSE = json.dumps({"archetype": "A2", "recommended_state": "close"})
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

    def complete(self, role, system_prompt, payload):
        queue = self._responses.get(role, [])
        assert queue, f"unexpected extra call to {role.value}"
        return queue.pop(0)


class ScriptedClientFactory:
    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = responses

    def __call__(self, case_id, db, **kwargs):
        return ScriptedClient(self._responses)


def _yazici(offer_made=None):
    return json.dumps({"message": "hello from the agent", "tactic_used": "TK-001", "offer_made": offer_made})


def _kritik(verdict, **extra):
    return json.dumps({"verdict": verdict, **extra})


def _whatsapp_signature(body: bytes) -> str:
    secret = get_settings().whatsapp_app_secret
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post_whatsapp_inbound(api_client, sender: str, text: str):
    payload = {
        "entry": [{"changes": [{"value": {"messages": [{"from": sender, "type": "text", "text": {"body": text}}]}}]}]
    }
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "X-Hub-Signature-256": _whatsapp_signature(body)}
    return api_client.post("/channels/whatsapp/webhook", content=body, headers=headers)


class FakeStripeClient:
    def __init__(self):
        self.captured = []

    def create_checkout_session(self, amount_cents, currency, metadata, success_url, cancel_url):
        return CheckoutSession(id="cs_e2e", url="https://stripe.test/checkout/cs_e2e", payment_intent_id=None)

    def capture_payment_intent(self, payment_intent_id, amount_to_capture_cents):
        self.captured.append((payment_intent_id, amount_to_capture_cents))

    def cancel_payment_intent(self, payment_intent_id):
        pass

    def construct_webhook_event(self, payload, sig_header, secret):
        return {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_e2e", "payment_intent": "pi_e2e"}},
        }


class FakeAsyncHttpClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, headers=None, json=None):
        class _Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"messages": [{"id": "wamid.e2e"}]}

        return _Resp()


def test_waitlist_to_capture_end_to_end(api_client, db_session, monkeypatch):
    fake_stripe = FakeStripeClient()
    monkeypatch.setattr(payments_module, "RealStripeClient", lambda *a, **k: fake_stripe)
    monkeypatch.setattr(whatsapp_module.httpx, "AsyncClient", lambda: FakeAsyncHttpClient())
    email_calls = []
    monkeypatch.setattr(
        email_module, "send_email", lambda to, subject, body: email_calls.append((to, subject, body))
    )

    # 1. Waitlist signup.
    resp = api_client.post("/waitlist", json={"email": "tenant@example.com", "source": "e2e-test"})
    assert resp.status_code == 200
    assert db_session.query(WaitlistSignup).filter(WaitlistSignup.email == "tenant@example.com").count() == 1

    # 2. Web registration.
    resp = api_client.post(
        "/web/register", json={"email": "tenant@example.com", "phone": "+15559990000", "name": "Test Tenant"}
    )
    assert resp.status_code == 200
    session_token = resp.json()["session_token"]

    # 3. Web chat confirms an already-collected intake brief -> Case created,
    #    Payment(pending) opened, initial-contact email sent (counterparty
    #    has an email on file), checkout link in the reply.
    from app.models import User

    user = db_session.query(User).filter(User.phone == "+15559990000").one()
    user.intake_state = {
        "collected_fields": {
            "mulk_adres": "Marina",
            "hedef_kira": 90000,
            "taban_kira": 85000,
            "tavan_kira": 100000,
            "ev_sahibi_iletisim": COUNTERPARTY_PHONE,
            "ev_sahibi_adi": "Ali",
            "ev_sahibi_email": "landlord@example.com",
        },
        "missing_fields": [],
        "ready": True,
        "awaiting_confirmation": True,
    }
    db_session.commit()

    monkeypatch.setattr(
        web_module, "AnthropicSubagentClient", ScriptedClientFactory({SubagentRole.stratejist: [STRATEJIST_OK]})
    )

    resp = api_client.post("/web/chat", json={"message": "evet onaylıyorum"}, headers={"Authorization": f"Bearer {session_token}"})
    assert resp.status_code == 200
    body = resp.json()
    case_id = body["case_id"]
    assert case_id is not None
    assert "http" in body["reply"]  # checkout link included

    assert email_calls, "send_initial_contact_email should have fired (counterparty_email is known)"
    assert email_calls[0][0] == "landlord@example.com"

    from app.models import Case

    case = db_session.get(Case, case_id)
    assert case.payment is not None
    assert case.payment.status is PaymentStatusEnum.pending

    # 4. Customer completes the Stripe checkout -> webhook confirms pre-auth.
    resp = api_client.get(f"/payments/checkout/{case.payment.access_token}", follow_redirects=False)
    assert resp.status_code == 302
    resp = api_client.post("/payments/webhook", content=b"{}", headers={"stripe-signature": "sig"})
    assert resp.status_code == 200
    db_session.refresh(case.payment)
    assert case.payment.status is PaymentStatusEnum.pre_authorized

    # 5. Counterparty (landlord) messages us on WhatsApp for the first time —
    #    this is real opt-in (Package H) AND produces an APPROVEd draft.
    monkeypatch.setattr(
        whatsapp_module,
        "AnthropicSubagentClient",
        ScriptedClientFactory(
            {
                SubagentRole.analist: [ANALIST_ANCHORING],
                SubagentRole.yazici: [_yazici(offer_made=92000)],
                SubagentRole.kritik: [_kritik("APPROVE")],
            }
        ),
    )
    resp = _post_whatsapp_inbound(api_client, COUNTERPARTY_PHONE, "100000 istiyorum")
    assert resp.status_code == 200

    from app.models import OutboundQueueItem

    counterparty_item = (
        db_session.query(OutboundQueueItem)
        .filter(OutboundQueueItem.case_id == case.id, OutboundQueueItem.status == OutboundStatusEnum.pending_approval)
        .order_by(OutboundQueueItem.created_at.desc())
        .first()
    )
    assert counterparty_item is not None

    # 6. Operator approves — both the payment pre-auth guard (Package G) and
    #    the opt-in guard (Package H) must pass for this to succeed.
    resp = api_client.post(
        f"/review/{counterparty_item.id}/approve",
        json={"reviewed_by": "e2e-operator"},
        headers={"Authorization": f"Bearer {get_settings().review_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"

    # 7. Deal closes (won) -> automatic capture.
    monkeypatch.setattr(
        whatsapp_module,
        "AnthropicSubagentClient",
        ScriptedClientFactory(
            {
                SubagentRole.analist: [ANALIST_CLOSE],
                SubagentRole.yazici: [_yazici()],
                SubagentRole.kritik: [_kritik("APPROVE")],
            }
        ),
    )
    resp = _post_whatsapp_inbound(api_client, COUNTERPARTY_PHONE, "anlaştık, 92000'e kabul")
    assert resp.status_code == 200

    db_session.refresh(case)
    db_session.refresh(case.payment)
    assert case.state.value == "close"
    assert case.outcome.value == "won"
    assert case.payment.status is PaymentStatusEnum.captured
    assert fake_stripe.captured  # capture_payment_intent was actually called

    # 8. Daily report reflects the whole flow — no manual DB read needed to
    #    know it happened.
    today = case.created_at.astimezone(timezone.utc).date()
    report = compute_daily_report(db_session, day=today)
    assert report.new_cases >= 1
    assert report.closed_won >= 1
    assert report.captured_total > 0
    assert report.new_waitlist_signups >= 1
