import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import ChannelEnum, StateEnum


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
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
