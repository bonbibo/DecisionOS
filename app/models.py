import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StateEnum(str, enum.Enum):
    """Negotiation lifecycle. Transitions are enforced by app.engine.NegotiationEngine."""

    discovery = "discovery"
    anchoring = "anchoring"
    counter = "counter"
    concession = "concession"
    close = "close"


class ChannelEnum(str, enum.Enum):
    whatsapp = "whatsapp"
    email = "email"
    web = "web"


class DirectionEnum(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class ActorEnum(str, enum.Enum):
    us = "us"
    counterparty = "counterparty"


class OutboundStatusEnum(str, enum.Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    edited = "edited"
    rejected = "rejected"
    sent = "sent"


class MessageKindEnum(str, enum.Enum):
    """Which conversation a Message belongs to: onboarding (no Case yet) or an
    active negotiation (tied to a Case)."""

    intake = "intake"
    negotiation = "negotiation"


class AudienceEnum(str, enum.Enum):
    """Who an outbound_queue item is addressed to."""

    counterparty = "counterparty"
    client = "client"


class OutcomeEnum(str, enum.Enum):
    """Set on Case once Analist's recommended_state distinguishes a real
    close from a walk-away — see app.orchestrator._apply_recommended_state."""

    won = "won"
    walked = "walked"


class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    pre_authorized = "pre_authorized"
    captured = "captured"
    canceled = "canceled"
    failed = "failed"


class EscalationCategoryEnum(str, enum.Enum):
    """Which Kritik checklist item (app/prompts/kritik.md) triggered an
    ESCALATE, or a generic bucket for the non-Kritik escalation paths (max
    revisions/replans exhausted, an unparseable subagent response). Set by
    app.orchestrator._categorize — see docs/MASTER-SPEC-v3.md Package K:
    this exists purely to make KR-003's phone-request threshold
    measurable, not to change any escalation behavior."""

    floor_violation = "floor_violation"  # madde 1
    info_leak = "info_leak"  # madde 2
    fabrication = "fabrication"  # madde 3
    unconditional_concession = "unconditional_concession"  # madde 4
    tactic_mismatch = "tactic_mismatch"  # madde 5
    premature_acceptance = "premature_acceptance"  # madde 6
    phone_request = "phone_request"  # madde 7, "telefon" alt dizesi
    escalation_signal_other = "escalation_signal_other"  # madde 7, diğer (hukuki/agresyon/kimlik)
    decision_conflict = "decision_conflict"  # madde 8
    other = "other"  # max revizyon/reject, parse hatası vb.


class OptInMethodEnum(str, enum.Enum):
    """How an OptIn record was created — an audit trail, not itself the
    guard's source of truth (see app.channels.whatsapp._has_valid_opt_in,
    which only trusts an actual inbound WhatsApp message)."""

    whatsapp_first_message = "whatsapp_first_message"
    email_link_click = "email_link_click"
    manual_operator = "manual_operator"


class User(Base):
    """The end customer — the person texting the agent on WhatsApp to ask for help."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    # Unique (Postgres allows multiple NULLs under a unique constraint, so
    # WhatsApp-only users with no email are unaffected) — this is now the
    # customer portal's login identifier, see app.auth / app/channels/web.py.
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="tr")

    # Bearer token for POST /web/chat, issued by POST /web/auth/verify-code
    # after a successful email OTP login (see app.auth, app/channels/web.py).
    web_session_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)

    # In-progress intake brief: {collected_fields, missing_fields, ready,
    # awaiting_confirmation}. Cleared once a Case is created. See app/intake.py.
    intake_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cases: Mapped[list["Case"]] = relationship(back_populates="user")
    messages: Mapped[list["Message"]] = relationship(back_populates="user")
    memory: Mapped[list["UserMemory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    llm_calls: Mapped[list["LLMCall"]] = relationship(back_populates="user")
    login_codes: Mapped[list["LoginCode"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserMemory(Base):
    """A durable fact learned about a user, carried across cases (e.g. `risk_toleransi: dusuk`)."""

    __tablename__ = "user_memory"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_memory_user_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="memory")


class WaitlistSignup(Base):
    """A landing-page waitlist signup (Package I) — deliberately separate
    from User: this is a pre-product demand signal, not a customer with a
    Case yet."""

    __tablename__ = "waitlist_signups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum, name="channel_enum"), nullable=False)
    # Playbook vertical, e.g. "kira-bae" — matches a vault/01-Playbooks/*.md `dikey`.
    vertical: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # True only for internal/demo cases — gates access to `durum: demo` vault/07-Fiyatlama/*.md
    # pricing (e.g. arac-bae) that real customers should never be quoted. See app/intake.py.
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty_contact: Mapped[str] = mapped_column(String(255), nullable=False)
    # Optional — enables Package H's email-first initial contact
    # (app.channels.email.send_initial_contact_email) when known.
    counterparty_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    state: Mapped[StateEnum] = mapped_column(
        Enum(StateEnum, name="state_enum"), nullable=False, default=StateEnum.discovery
    )

    item_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    min_acceptable_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Stratejist's plan JSON (anchor/target/floor/concession_ladder/...); set at case
    # open and recomputed after a Kritik REJECT verdict. See app/orchestrator.py.
    plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # {"incoming_message": str, "human_answers": [{"answer": str, "answered_by": str|None,
    # "answered_at": iso str}, ...]} — set when an ESCALATE happens, appended to on every
    # POST /review/case/{id}/answer resume. Also the human-in-the-loop half of the dataset
    # trail (the LLM-side half is LLMCall.request_payload/response_text). See
    # app.orchestrator.resume_after_escalation.
    escalation_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Which Kritik checklist item (or generic bucket) triggered the most
    # recent escalation — see EscalationCategoryEnum. Purely for measuring
    # KR-003's voice-channel threshold; doesn't affect any behavior.
    escalation_category: Mapped[EscalationCategoryEnum | None] = mapped_column(
        Enum(EscalationCategoryEnum, name="escalation_category_enum"), nullable=True
    )
    # Set once Analist's recommended_state distinguishes a real close (won)
    # from a walk-away (walked) — None while still open. See
    # app.orchestrator._apply_recommended_state, app.payments.
    outcome: Mapped[OutcomeEnum | None] = mapped_column(Enum(OutcomeEnum, name="outcome_enum"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="cases")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="Message.created_at"
    )
    offers: Mapped[list["Offer"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="Offer.round_number"
    )
    llm_calls: Mapped[list["LLMCall"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="LLMCall.created_at"
    )
    outbound_queue: Mapped[list["OutboundQueueItem"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="OutboundQueueItem.created_at"
    )
    payment: Mapped["Payment | None"] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Negotiation messages are tied to a Case; intake messages (no Case yet)
    # are tied to a User instead — exactly one of the two is set.
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    kind: Mapped[MessageKindEnum] = mapped_column(
        Enum(MessageKindEnum, name="message_kind_enum"), nullable=False, default=MessageKindEnum.negotiation
    )
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum, name="channel_enum"), nullable=False)
    direction: Mapped[DirectionEnum] = mapped_column(Enum(DirectionEnum, name="direction_enum"), nullable=False)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case | None"] = relationship(back_populates="messages")
    user: Mapped["User | None"] = relationship(back_populates="messages")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    actor: Mapped[ActorEnum] = mapped_column(Enum(ActorEnum, name="actor_enum"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="offers")


class LLMCall(Base):
    """One subagent completion call, logged for cost/latency tracking."""

    __tablename__ = "llm_calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Intake calls (SubagentRole.intake) happen before any Case exists, so
    # case_id is nullable; user_id is set whenever the caller is known.
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # a SubagentRole value
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Full call I/O, kept as a dataset for later analysis/fine-tuning — not just
    # the token/latency metrics above. See app/llm.py::AnthropicSubagentClient.complete.
    request_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case | None"] = relationship(back_populates="llm_calls")
    user: Mapped["User | None"] = relationship(back_populates="llm_calls")


class OutboundQueueItem(Base):
    """A Kritik-approved draft awaiting human approval before it's actually sent."""

    __tablename__ = "outbound_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum, name="channel_enum"), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    tactic_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    audience: Mapped[AudienceEnum] = mapped_column(
        Enum(AudienceEnum, name="audience_enum"), nullable=False, default=AudienceEnum.counterparty
    )

    status: Mapped[OutboundStatusEnum] = mapped_column(
        Enum(OutboundStatusEnum, name="outbound_status_enum"),
        nullable=False,
        default=OutboundStatusEnum.pending_approval,
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="outbound_queue")


class Payment(Base):
    """A Stripe pre-auth opened at case creation, captured (or canceled) once
    the case closes. See app/payments.py, docs/MASTER-SPEC-v3.md Package G."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Single-use token embedded in the checkout link sent to the customer
    # (POST /payments/checkout/{access_token}) — not a session/API auth token.
    access_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    checkout_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Pre-auth hold amount == vault pricing's min_ucret (a floor, not a
    # ceiling) — V1 simplification, see docs/MASTER-SPEC-v3.md Package G:
    # capture is capped at this amount even if the computed fee is higher.
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    captured_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum, name="payment_status_enum"), nullable=False, default=PaymentStatusEnum.pending
    )
    # Set if the computed success fee exceeded `amount` at capture time — the
    # shortfall needs a manual follow-up charge (out of scope for V1 code).
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    pre_authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["Case"] = relationship(back_populates="payment")


class OptIn(Base):
    """An audit record of consent to receive a WhatsApp message from us —
    see app.channels.whatsapp._has_valid_opt_in for the actual guard logic
    (which only trusts a real inbound message, not this table alone)."""

    __tablename__ = "opt_ins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)

    contact: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum, name="channel_enum"), nullable=False)
    method: Mapped[OptInMethodEnum] = mapped_column(Enum(OptInMethodEnum, name="opt_in_method_enum"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginCode(Base):
    """A one-time 6-digit email login code — see app.auth.create_login_code/
    verify_login_code. Replaces the old "email+phone, no verification"
    trust model for the customer portal (app/portal/, app/channels/web.py's
    POST /web/auth/request-code -> POST /web/auth/verify-code)."""

    __tablename__ = "login_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # sha256 hex — never store plaintext
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Failed-verify counter — a code is rejected once this hits MAX_ATTEMPTS
    # (app.auth), a basic brute-force guard on the 6-digit space.
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="login_codes")
