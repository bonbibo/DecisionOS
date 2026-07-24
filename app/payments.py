"""Stripe pre-auth -> capture (draft — Package G).

A card is pre-authorized (held, not charged) when a case opens; the actual
success fee is captured only once the case closes as `won` (never on a
`walked` outcome, where the hold is released instead). See
docs/MASTER-SPEC-v3.md Package G for the full design, including the two
explicitly-approved V1 simplifications:
  - the pre-auth amount is vault pricing's `min_ucret` (a floor, not a
    ceiling) — if the computed fee at close exceeds it, capture is capped
    at the pre-authorized amount and `Payment.note` records the shortfall
    for manual follow-up.
  - the opt-in guard's real-world equivalent for money: `require_pre_auth`
    blocks a counterparty send the same way app.channels.whatsapp's opt-in
    guard (Package H) blocks an unconsented one.

Same injectable-client seam as AnthropicSubagentClient: every function here
takes an optional `stripe_client` (a StripeClient), defaulting to
RealStripeClient() when omitted. Every function that only mutates the ORM
graph (create_pre_auth, capture_for_won_case, cancel_for_walked_case,
handle_turn_outcome) takes no `db` and does not commit — same "caller
persists" contract as app.engine.record_offer/record_message and
app.orchestrator.run_turn. Only the two HTTP endpoints (which have no other
caller to persist for them) commit directly, like app.review's endpoints.
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import ActorEnum, Case, OutcomeEnum, Payment, PaymentStatusEnum, StateEnum
from app.vault import VaultReader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class PreAuthRequiredError(Exception):
    """Raised by require_pre_auth — a priced, non-demo case's counterparty
    draft can't be sent without at least a pre-authorized Payment."""

    def __init__(self, case_id):
        self.case_id = case_id
        super().__init__(f"case {case_id} has no pre-authorized payment")


@dataclass
class CheckoutSession:
    id: str
    url: str
    payment_intent_id: str | None = None


class StripeClient(Protocol):
    """The seam a real Stripe integration implements — mirrors
    app.subagents.SubagentClient / AnthropicSubagentClient's shape."""

    def create_checkout_session(
        self, amount_cents: int, currency: str, metadata: dict, success_url: str, cancel_url: str
    ) -> CheckoutSession: ...

    def capture_payment_intent(self, payment_intent_id: str, amount_to_capture_cents: int) -> None: ...

    def cancel_payment_intent(self, payment_intent_id: str) -> None: ...

    def construct_webhook_event(self, payload: bytes, sig_header: str | None, secret: str) -> Any: ...


class RealStripeClient:
    """StripeClient backed by the real `stripe` SDK."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        stripe.api_key = self.settings.stripe_secret_key

    def create_checkout_session(
        self, amount_cents: int, currency: str, metadata: dict, success_url: str, cancel_url: str
    ) -> CheckoutSession:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_intent_data={"capture_method": "manual"},
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "unit_amount": amount_cents,
                        "product_data": {"name": "DecisionOS negotiation fee (pre-authorization)"},
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        return CheckoutSession(id=session.id, url=session.url, payment_intent_id=session.get("payment_intent"))

    def capture_payment_intent(self, payment_intent_id: str, amount_to_capture_cents: int) -> None:
        stripe.PaymentIntent.capture(payment_intent_id, amount_to_capture=amount_to_capture_cents)

    def cancel_payment_intent(self, payment_intent_id: str) -> None:
        stripe.PaymentIntent.cancel(payment_intent_id)

    def construct_webhook_event(self, payload: bytes, sig_header: str | None, secret: str) -> Any:
        return stripe.Webhook.construct_event(payload, sig_header, secret)


def _pricing_for_vertical(vault_dir: str, dikey: str) -> dict | None:
    """Active (durum: aktif) vault/07-Fiyatlama/<dikey>.md frontmatter, or
    None (unpriced vertical — e.g. a demo-only one)."""
    context = VaultReader(vault_dir).read_folder("07-Fiyatlama", recursive=False)
    for doc in context.documents:
        frontmatter = doc.frontmatter or {}
        if frontmatter.get("dikey") == dikey and frontmatter.get("durum") == "aktif" and "fiyat_id" in frontmatter:
            return frontmatter
    return None


def create_pre_auth(case: Case, pricing: dict) -> Payment:
    """Opens a `pending` Payment for `case` (no card on file yet — that
    happens when the customer completes the checkout link built from
    `access_token`, see checkout_redirect). Caller persists via `db.add`ing
    `case` (or its own session) same as app.engine.record_offer."""
    payment = Payment(
        access_token=secrets.token_urlsafe(32),
        amount=float(pricing["min_ucret"]),
        currency=pricing.get("para_birimi", "AED"),
        status=PaymentStatusEnum.pending,
    )
    case.payment = payment
    return payment


def checkout_link(payment: Payment, base_url: str) -> str:
    return f"{base_url.rstrip('/')}/payments/checkout/{payment.access_token}"


def compute_success_fee(case: Case, pricing: dict) -> float:
    """V1 heuristic (docs/MASTER-SPEC-v3.md Package G): initial ask = the
    counterparty's first recorded Offer, or the very first Offer at all if
    the counterparty never stated one; final price = the most recently
    recorded Offer by either side. savings = max(0, initial_ask -
    final_price); fee = max(min_ucret, savings * basari_yuzdesi / 100).
    Falls back to min_ucret alone if there's no offer history at all."""
    offers = sorted(case.offers, key=lambda o: o.round_number)
    if not offers:
        return float(pricing["min_ucret"])

    counterparty_offers = [o for o in offers if o.actor == ActorEnum.counterparty]
    initial_ask = float(counterparty_offers[0].price) if counterparty_offers else float(offers[0].price)
    final_price = float(offers[-1].price)
    savings = max(0.0, initial_ask - final_price)
    fee = savings * float(pricing["basari_yuzdesi"]) / 100
    return max(float(pricing["min_ucret"]), fee)


def capture_for_won_case(
    case: Case, stripe_client: StripeClient | None = None, vault_dir: str = "vault"
) -> Payment | None:
    """Captures the pre-authorized hold once `case` closes as `won`. None
    (no-op) if there's nothing pre-authorized to capture — most commonly a
    demo/unpriced case that never opened a Payment."""
    payment = case.payment
    if payment is None or payment.status != PaymentStatusEnum.pre_authorized:
        return None
    if not payment.stripe_payment_intent_id:
        logger.error("Payment %s is pre_authorized but has no payment_intent_id — cannot capture", payment.id)
        return None

    stripe_client = stripe_client or RealStripeClient()
    pricing = _pricing_for_vertical(vault_dir, case.vertical) if case.vertical else None
    fee = compute_success_fee(case, pricing) if pricing else float(payment.amount)

    capture_amount = min(fee, float(payment.amount))
    if fee > float(payment.amount):
        payment.note = (
            f"Computed fee {fee:.2f} {payment.currency} exceeded the pre-authorized hold "
            f"{float(payment.amount):.2f} {payment.currency} — capture capped, manual follow-up needed."
        )

    stripe_client.capture_payment_intent(payment.stripe_payment_intent_id, int(round(capture_amount * 100)))

    payment.status = PaymentStatusEnum.captured
    payment.captured_amount = capture_amount
    payment.captured_at = datetime.now(timezone.utc)
    return payment


def cancel_for_walked_case(case: Case, stripe_client: StripeClient | None = None) -> Payment | None:
    """Releases the pre-authorized hold once `case` closes as `walked`."""
    payment = case.payment
    if payment is None or payment.status != PaymentStatusEnum.pre_authorized:
        return None
    if not payment.stripe_payment_intent_id:
        return None

    stripe_client = stripe_client or RealStripeClient()
    stripe_client.cancel_payment_intent(payment.stripe_payment_intent_id)

    payment.status = PaymentStatusEnum.canceled
    payment.canceled_at = datetime.now(timezone.utc)
    return payment


def handle_turn_outcome(
    case: Case, stripe_client: StripeClient | None = None, vault_dir: str = "vault"
) -> Payment | None:
    """Call right after run_turn()/resume_after_escalation() in every
    negotiation-turn handler (WhatsApp, web, the escalation-answer
    endpoint) — captures/cancels the pre-auth the instant a case actually
    closes. A no-op unless the case just closed with a known outcome."""
    if case.state is not StateEnum.close:
        return None
    if case.outcome is OutcomeEnum.won:
        return capture_for_won_case(case, stripe_client, vault_dir)
    if case.outcome is OutcomeEnum.walked:
        return cancel_for_walked_case(case, stripe_client)
    return None


def require_pre_auth(case: Case, vault_dir: str = "vault") -> None:
    """Raises PreAuthRequiredError if `case`'s vertical is priced
    (non-demo, `durum: aktif` vault pricing exists) and its Payment hasn't
    reached at least `pre_authorized`. Demo cases and unpriced verticals are
    exempt — called from app.review/app.admin's approve() for
    audience=counterparty sends only (see there)."""
    if case.is_demo or not case.vertical:
        return
    if _pricing_for_vertical(vault_dir, case.vertical) is None:
        return
    if case.payment is None or case.payment.status not in (
        PaymentStatusEnum.pre_authorized,
        PaymentStatusEnum.captured,
    ):
        raise PreAuthRequiredError(case.id)


# --- HTTP endpoints ---


def _get_payment_by_token(db: Session, token: str) -> Payment:
    payment = db.execute(select(Payment).where(Payment.access_token == token)).scalars().first()
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    return payment


@router.get("/checkout/{token}")
def checkout_redirect(token: str, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """Public, no auth (the token itself is the credential — single-use,
    unguessable). Creates the actual Stripe Checkout Session on first visit
    and redirects there; reuses the stored URL on any later visit (V1
    doesn't handle Stripe's own ~24h checkout URL expiry — a known
    limitation, see docs/MASTER-SPEC-v3.md Package G)."""
    payment = _get_payment_by_token(db, token)
    if payment.checkout_url is None:
        base = str(request.base_url).rstrip("/")
        session = RealStripeClient().create_checkout_session(
            amount_cents=int(round(float(payment.amount) * 100)),
            currency=payment.currency,
            metadata={"case_id": str(payment.case_id), "payment_id": str(payment.id)},
            success_url=f"{base}/payments/checkout/{token}/done",
            cancel_url=f"{base}/payments/checkout/{token}",
        )
        payment.stripe_checkout_session_id = session.id
        payment.checkout_url = session.url
        db.commit()
    return RedirectResponse(url=payment.checkout_url, status_code=302)


@router.get("/checkout/{token}/done", response_class=HTMLResponse)
def checkout_done() -> HTMLResponse:
    return HTMLResponse(
        "<h1>Teşekkürler</h1><p>Kart doğrulaması alındı. Ekibimiz kısa süre içinde dönecek. / "
        "Thank you — your card has been verified. We'll be in touch shortly.</p>"
    )


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Stripe's own push notifications — mirrors app.channels.whatsapp's
    signature-verification pattern exactly (Stripe-Signature header /
    STRIPE_WEBHOOK_SECRET here, X-Hub-Signature-256 / WHATSAPP_APP_SECRET
    there)."""
    body = await request.body()
    settings = get_settings()
    try:
        event = RealStripeClient().construct_webhook_event(
            body, request.headers.get("stripe-signature"), settings.stripe_webhook_secret
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid webhook signature") from exc

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        payment = db.execute(
            select(Payment).where(Payment.stripe_checkout_session_id == data["id"])
        ).scalars().first()
        if payment is not None:
            payment.stripe_payment_intent_id = data.get("payment_intent")
            payment.status = PaymentStatusEnum.pre_authorized
            payment.pre_authorized_at = datetime.now(timezone.utc)
            db.commit()
    elif event_type == "payment_intent.payment_failed":
        payment = db.execute(
            select(Payment).where(Payment.stripe_payment_intent_id == data["id"])
        ).scalars().first()
        if payment is not None:
            payment.status = PaymentStatusEnum.failed
            db.commit()

    return {"status": "received"}
