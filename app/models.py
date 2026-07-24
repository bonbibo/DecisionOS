import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
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


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum, name="channel_enum"), nullable=False)
    # Playbook vertical, e.g. "kira-bae" — matches a vault/01-Playbooks/*.md `dikey`.
    vertical: Mapped[str | None] = mapped_column(String(100), nullable=True)
    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty_contact: Mapped[str] = mapped_column(String(255), nullable=False)

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

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum, name="channel_enum"), nullable=False)
    direction: Mapped[DirectionEnum] = mapped_column(Enum(DirectionEnum, name="direction_enum"), nullable=False)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="messages")


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
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # a SubagentRole value
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="llm_calls")


class OutboundQueueItem(Base):
    """A Kritik-approved draft awaiting human approval before it's actually sent."""

    __tablename__ = "outbound_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum, name="channel_enum"), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    tactic_used: Mapped[str | None] = mapped_column(String(50), nullable=True)

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
