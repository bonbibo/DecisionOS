import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ActorEnum, ChannelEnum, DirectionEnum, OutboundStatusEnum, StateEnum


class CaseCreate(BaseModel):
    channel: ChannelEnum
    vertical: str | None = None
    counterparty_name: str | None = None
    counterparty_contact: str
    item_description: str | None = None
    target_price: float | None = None
    min_acceptable_price: float | None = None
    max_price: float | None = None


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: ChannelEnum
    vertical: str | None
    counterparty_name: str | None
    counterparty_contact: str
    state: StateEnum
    item_description: str | None
    target_price: float | None
    min_acceptable_price: float | None
    max_price: float | None
    plan: dict | None
    escalated: bool
    escalation_reason: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class OutboundQueueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    channel: ChannelEnum
    recipient: str
    message: str
    tactic_used: str | None
    status: OutboundStatusEnum
    reviewed_by: str | None
    reviewed_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


class ReviewApproveRequest(BaseModel):
    reviewed_by: str | None = None


class ReviewEditRequest(BaseModel):
    message: str
    reviewed_by: str | None = None


class ReviewRejectRequest(BaseModel):
    reviewed_by: str | None = None


class CaseAnswerRequest(BaseModel):
    answer: str
    reviewed_by: str | None = None


class WebRegisterRequest(BaseModel):
    email: str
    phone: str
    name: str | None = None


class WebRegisterResponse(BaseModel):
    user_id: uuid.UUID
    session_token: str


class WebChatRequest(BaseModel):
    message: str


class WebChatResponse(BaseModel):
    reply: str
    case_id: uuid.UUID | None = None
    state: StateEnum | None = None
    escalated: bool = False


class TimelineMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    direction: DirectionEnum
    content: str
    created_at: datetime


class TimelineOfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor: ActorEnum
    round_number: int
    price: float
    currency: str
    created_at: datetime


class CaseTimelineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    state: StateEnum
    escalated: bool
    escalation_reason: str | None
    messages: list[TimelineMessageRead]
    offers: list[TimelineOfferRead]


class WaitlistRequest(BaseModel):
    email: str
    phone: str | None = None
    note: str | None = None
    source: str | None = None


class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
