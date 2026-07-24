import app.payments as payments_module
from app.models import ActorEnum, Offer, OutcomeEnum, Payment, PaymentStatusEnum, StateEnum
from app.payments import (
    CheckoutSession,
    PreAuthRequiredError,
    cancel_for_walked_case,
    capture_for_won_case,
    checkout_link,
    compute_success_fee,
    create_pre_auth,
    handle_turn_outcome,
    require_pre_auth,
)

KIRA_BAE_PRICING = {"fiyat_id": "FY-kira-bae", "dikey": "kira-bae", "basari_yuzdesi": 25, "min_ucret": 500, "para_birimi": "AED", "durum": "aktif"}


class FakeStripeClient:
    def __init__(self, checkout_session_id="cs_fake", checkout_url="https://stripe.test/checkout/cs_fake"):
        self.checkout_session_id = checkout_session_id
        self.checkout_url = checkout_url
        self.captured: list[tuple[str, int]] = []
        self.canceled: list[str] = []

    def create_checkout_session(self, amount_cents, currency, metadata, success_url, cancel_url):
        return CheckoutSession(id=self.checkout_session_id, url=self.checkout_url, payment_intent_id="pi_fake")

    def capture_payment_intent(self, payment_intent_id, amount_to_capture_cents):
        self.captured.append((payment_intent_id, amount_to_capture_cents))

    def cancel_payment_intent(self, payment_intent_id):
        self.canceled.append(payment_intent_id)

    def construct_webhook_event(self, payload, sig_header, secret):
        raise NotImplementedError


def _offer(case, actor, price, round_number):
    case.offers.append(Offer(actor=actor, price=price, round_number=round_number, currency="AED"))


# --- create_pre_auth / checkout_link ---


def test_create_pre_auth_sets_amount_from_min_ucret_and_pending_status(new_case):
    payment = create_pre_auth(new_case, KIRA_BAE_PRICING)

    assert payment.amount == 500
    assert payment.currency == "AED"
    assert payment.status is PaymentStatusEnum.pending
    assert payment.access_token
    assert new_case.payment is payment


def test_checkout_link_builds_url_from_base_and_token():
    payment = Payment(access_token="tok123", amount=500, currency="AED")
    assert checkout_link(payment, "http://localhost:8000/") == "http://localhost:8000/payments/checkout/tok123"


# --- compute_success_fee ---


def test_compute_success_fee_no_offers_falls_back_to_min_ucret(new_case):
    assert compute_success_fee(new_case, KIRA_BAE_PRICING) == 500


def test_compute_success_fee_uses_counterparty_first_and_last_offer(new_case):
    _offer(new_case, ActorEnum.counterparty, 100000, 1)
    _offer(new_case, ActorEnum.us, 90000, 2)
    _offer(new_case, ActorEnum.counterparty, 92000, 3)

    # savings = 100000 - 92000 = 8000; fee = 8000 * 25% = 2000 > min_ucret(500)
    assert compute_success_fee(new_case, KIRA_BAE_PRICING) == 2000


def test_compute_success_fee_floors_at_min_ucret_when_savings_small(new_case):
    _offer(new_case, ActorEnum.counterparty, 100000, 1)
    _offer(new_case, ActorEnum.us, 99900, 2)

    # savings = 100 -> fee = 25 < min_ucret(500)
    assert compute_success_fee(new_case, KIRA_BAE_PRICING) == 500


def test_compute_success_fee_no_counterparty_offer_uses_first_offer_as_ask(new_case):
    _offer(new_case, ActorEnum.us, 90000, 1)
    _offer(new_case, ActorEnum.us, 88000, 2)

    # initial_ask falls back to the very first offer (90000); savings = 2000; fee = 500
    assert compute_success_fee(new_case, KIRA_BAE_PRICING) == 500


# --- capture_for_won_case / cancel_for_walked_case ---


def test_capture_for_won_case_returns_none_without_payment(new_case):
    assert capture_for_won_case(new_case) is None


def test_capture_for_won_case_returns_none_when_not_pre_authorized(new_case):
    payment = create_pre_auth(new_case, KIRA_BAE_PRICING)
    assert payment.status is PaymentStatusEnum.pending
    assert capture_for_won_case(new_case) is None


def test_capture_for_won_case_captures_full_fee_within_hold(new_case, tmp_path):
    (tmp_path / "07-Fiyatlama").mkdir()
    (tmp_path / "07-Fiyatlama" / "kira-bae.md").write_text(
        "---\nfiyat_id: FY-kira-bae\ndikey: kira-bae\ndurum: aktif\nbasari_yuzdesi: 25\nmin_ucret: 500\n"
        "para_birimi: AED\n---\nbody\n",
        encoding="utf-8",
    )
    new_case.vertical = "kira-bae"
    payment = create_pre_auth(new_case, {"min_ucret": 5000, "para_birimi": "AED"})
    payment.status = PaymentStatusEnum.pre_authorized
    payment.stripe_payment_intent_id = "pi_123"
    _offer(new_case, ActorEnum.counterparty, 100000, 1)
    _offer(new_case, ActorEnum.us, 92000, 2)
    fake = FakeStripeClient()

    result = capture_for_won_case(new_case, stripe_client=fake, vault_dir=str(tmp_path))

    assert result is payment
    assert payment.status is PaymentStatusEnum.captured
    assert payment.captured_amount == 2000  # (100000-92000)*25% = 2000, within the 5000 hold
    assert payment.note is None
    assert fake.captured == [("pi_123", 200000)]  # cents


def test_capture_for_won_case_caps_at_pre_auth_amount_and_notes_shortfall(new_case, tmp_path):
    (tmp_path / "07-Fiyatlama").mkdir()
    (tmp_path / "07-Fiyatlama" / "kira-bae.md").write_text(
        "---\nfiyat_id: FY-kira-bae\ndikey: kira-bae\ndurum: aktif\nbasari_yuzdesi: 25\nmin_ucret: 500\n"
        "para_birimi: AED\n---\nbody\n",
        encoding="utf-8",
    )
    new_case.vertical = "kira-bae"
    payment = create_pre_auth(new_case, {"min_ucret": 500, "para_birimi": "AED"})  # small hold
    payment.status = PaymentStatusEnum.pre_authorized
    payment.stripe_payment_intent_id = "pi_123"
    _offer(new_case, ActorEnum.counterparty, 200000, 1)
    _offer(new_case, ActorEnum.us, 100000, 2)  # savings=100000 -> fee=25000, way over the 500 hold
    fake = FakeStripeClient()

    result = capture_for_won_case(new_case, stripe_client=fake, vault_dir=str(tmp_path))

    assert result.status is PaymentStatusEnum.captured
    assert result.captured_amount == 500  # capped at the pre-authorized hold
    assert "exceeded" in result.note
    assert fake.captured == [("pi_123", 50000)]


def test_capture_for_won_case_no_payment_intent_returns_none(new_case):
    payment = create_pre_auth(new_case, KIRA_BAE_PRICING)
    payment.status = PaymentStatusEnum.pre_authorized
    assert capture_for_won_case(new_case, stripe_client=FakeStripeClient()) is None


def test_cancel_for_walked_case_releases_hold(new_case):
    payment = create_pre_auth(new_case, KIRA_BAE_PRICING)
    payment.status = PaymentStatusEnum.pre_authorized
    payment.stripe_payment_intent_id = "pi_123"
    fake = FakeStripeClient()

    result = cancel_for_walked_case(new_case, stripe_client=fake)

    assert result is payment
    assert payment.status is PaymentStatusEnum.canceled
    assert fake.canceled == ["pi_123"]


def test_cancel_for_walked_case_returns_none_without_payment(new_case):
    assert cancel_for_walked_case(new_case) is None


# --- handle_turn_outcome ---


def test_handle_turn_outcome_noop_when_not_closed(new_case):
    new_case.state = StateEnum.counter
    new_case.outcome = OutcomeEnum.won
    assert handle_turn_outcome(new_case) is None


def test_handle_turn_outcome_captures_on_won(new_case, tmp_path):
    (tmp_path / "07-Fiyatlama").mkdir()
    (tmp_path / "07-Fiyatlama" / "kira-bae.md").write_text(
        "---\nfiyat_id: FY-kira-bae\ndikey: kira-bae\ndurum: aktif\nbasari_yuzdesi: 25\nmin_ucret: 500\n"
        "para_birimi: AED\n---\nbody\n",
        encoding="utf-8",
    )
    new_case.vertical = "kira-bae"
    new_case.state = StateEnum.close
    new_case.outcome = OutcomeEnum.won
    payment = create_pre_auth(new_case, {"min_ucret": 500, "para_birimi": "AED"})
    payment.status = PaymentStatusEnum.pre_authorized
    payment.stripe_payment_intent_id = "pi_123"
    fake = FakeStripeClient()

    result = handle_turn_outcome(new_case, stripe_client=fake, vault_dir=str(tmp_path))

    assert result.status is PaymentStatusEnum.captured


def test_handle_turn_outcome_cancels_on_walked(new_case):
    new_case.state = StateEnum.close
    new_case.outcome = OutcomeEnum.walked
    payment = create_pre_auth(new_case, KIRA_BAE_PRICING)
    payment.status = PaymentStatusEnum.pre_authorized
    payment.stripe_payment_intent_id = "pi_123"

    result = handle_turn_outcome(new_case, stripe_client=FakeStripeClient())

    assert result.status is PaymentStatusEnum.canceled


def test_handle_turn_outcome_noop_when_no_outcome(new_case):
    new_case.state = StateEnum.close
    new_case.outcome = None
    assert handle_turn_outcome(new_case) is None


# --- require_pre_auth ---


def test_require_pre_auth_exempts_demo_case(new_case):
    new_case.is_demo = True
    new_case.vertical = "kira-bae"
    require_pre_auth(new_case, vault_dir="vault")  # no raise


def test_require_pre_auth_exempts_case_without_vertical(new_case):
    new_case.vertical = None
    require_pre_auth(new_case, vault_dir="vault")  # no raise


def test_require_pre_auth_exempts_unpriced_vertical(new_case, tmp_path):
    (tmp_path / "07-Fiyatlama").mkdir()
    new_case.vertical = "some-other-vertical"
    require_pre_auth(new_case, vault_dir=str(tmp_path))  # no raise


def test_require_pre_auth_raises_without_payment(new_case, tmp_path):
    (tmp_path / "07-Fiyatlama").mkdir()
    (tmp_path / "07-Fiyatlama" / "kira-bae.md").write_text(
        "---\nfiyat_id: FY-kira-bae\ndikey: kira-bae\ndurum: aktif\nmin_ucret: 500\n---\nbody\n", encoding="utf-8"
    )
    new_case.vertical = "kira-bae"
    try:
        require_pre_auth(new_case, vault_dir=str(tmp_path))
        assert False, "expected PreAuthRequiredError"
    except PreAuthRequiredError:
        pass


def test_require_pre_auth_passes_when_pre_authorized(new_case, tmp_path):
    (tmp_path / "07-Fiyatlama").mkdir()
    (tmp_path / "07-Fiyatlama" / "kira-bae.md").write_text(
        "---\nfiyat_id: FY-kira-bae\ndikey: kira-bae\ndurum: aktif\nmin_ucret: 500\n---\nbody\n", encoding="utf-8"
    )
    new_case.vertical = "kira-bae"
    payment = create_pre_auth(new_case, KIRA_BAE_PRICING)
    payment.status = PaymentStatusEnum.pre_authorized
    require_pre_auth(new_case, vault_dir=str(tmp_path))  # no raise


# --- endpoints ---


def test_checkout_redirect_404_for_unknown_token(api_client):
    resp = api_client.get("/payments/checkout/does-not-exist", follow_redirects=False)
    assert resp.status_code == 404


def test_checkout_redirect_creates_session_and_redirects(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    payment = create_pre_auth(case, KIRA_BAE_PRICING)
    db_session.add(payment)
    db_session.commit()

    fake = FakeStripeClient(checkout_url="https://stripe.test/checkout/abc")
    monkeypatch.setattr(payments_module, "RealStripeClient", lambda *a, **k: fake)

    resp = api_client.get(f"/payments/checkout/{payment.access_token}", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"] == "https://stripe.test/checkout/abc"
    db_session.refresh(payment)
    assert payment.checkout_url == "https://stripe.test/checkout/abc"
    assert payment.stripe_checkout_session_id == "cs_fake"


def test_checkout_redirect_reuses_stored_url_on_second_visit(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    payment = create_pre_auth(case, KIRA_BAE_PRICING)
    db_session.add(payment)
    db_session.commit()

    calls = []

    class CountingFakeStripeClient(FakeStripeClient):
        def create_checkout_session(self, *a, **k):
            calls.append(1)
            return super().create_checkout_session(*a, **k)

    monkeypatch.setattr(payments_module, "RealStripeClient", lambda *a, **k: CountingFakeStripeClient())

    api_client.get(f"/payments/checkout/{payment.access_token}", follow_redirects=False)
    api_client.get(f"/payments/checkout/{payment.access_token}", follow_redirects=False)

    assert len(calls) == 1


def test_checkout_done_returns_200(api_client):
    resp = api_client.get("/payments/checkout/anything/done")
    assert resp.status_code == 200


def test_webhook_invalid_signature_rejected(api_client, monkeypatch):
    class RaisingStripeClient(FakeStripeClient):
        def construct_webhook_event(self, payload, sig_header, secret):
            raise ValueError("bad signature")

    monkeypatch.setattr(payments_module, "RealStripeClient", lambda *a, **k: RaisingStripeClient())

    resp = api_client.post("/payments/webhook", content=b"{}", headers={"stripe-signature": "bad"})
    assert resp.status_code == 401


def test_webhook_checkout_completed_sets_pre_authorized(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    payment = create_pre_auth(case, KIRA_BAE_PRICING)
    payment.stripe_checkout_session_id = "cs_fake"
    db_session.add(payment)
    db_session.commit()

    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_fake", "payment_intent": "pi_fake"}},
    }

    class EventStripeClient(FakeStripeClient):
        def construct_webhook_event(self, payload, sig_header, secret):
            return event

    monkeypatch.setattr(payments_module, "RealStripeClient", lambda *a, **k: EventStripeClient())

    resp = api_client.post("/payments/webhook", content=b"{}", headers={"stripe-signature": "ok"})

    assert resp.status_code == 200
    db_session.refresh(payment)
    assert payment.status is PaymentStatusEnum.pre_authorized
    assert payment.stripe_payment_intent_id == "pi_fake"
    assert payment.pre_authorized_at is not None


def test_webhook_payment_failed_sets_failed(api_client, make_case, db_session, monkeypatch):
    case = make_case()
    payment = create_pre_auth(case, KIRA_BAE_PRICING)
    payment.stripe_payment_intent_id = "pi_fake"
    db_session.add(payment)
    db_session.commit()

    event = {"type": "payment_intent.payment_failed", "data": {"object": {"id": "pi_fake"}}}

    class EventStripeClient(FakeStripeClient):
        def construct_webhook_event(self, payload, sig_header, secret):
            return event

    monkeypatch.setattr(payments_module, "RealStripeClient", lambda *a, **k: EventStripeClient())

    resp = api_client.post("/payments/webhook", content=b"{}", headers={"stripe-signature": "ok"})

    assert resp.status_code == 200
    db_session.refresh(payment)
    assert payment.status is PaymentStatusEnum.failed
