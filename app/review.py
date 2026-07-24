"""Human-in-the-loop review queue for Kritik-approved drafts (V1: plain REST).

Every draft run_turn approves lands in outbound_queue as pending_approval —
nothing is sent automatically. A human calls one of these three endpoints;
only approve actually sends (currently WhatsApp only).
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.channels import whatsapp
from app.database import get_db
from app.models import ChannelEnum, OutboundQueueItem, OutboundStatusEnum
from app.schemas import OutboundQueueRead, ReviewApproveRequest, ReviewEditRequest, ReviewRejectRequest

router = APIRouter(prefix="/review", tags=["review"])

_ACTIONABLE_STATUSES = {OutboundStatusEnum.pending_approval, OutboundStatusEnum.edited}


def _get_item(db: Session, msg_id: uuid.UUID) -> OutboundQueueItem:
    item = db.get(OutboundQueueItem, msg_id)
    if item is None:
        raise HTTPException(status_code=404, detail="outbound queue item not found")
    return item


@router.post("/{msg_id}/approve", response_model=OutboundQueueRead)
async def approve(msg_id: uuid.UUID, body: ReviewApproveRequest, db: Session = Depends(get_db)) -> OutboundQueueItem:
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    if item.channel is not ChannelEnum.whatsapp:
        raise HTTPException(status_code=501, detail=f"sending for channel '{item.channel.value}' isn't wired up yet")

    await whatsapp.send_text_message(item.recipient, item.message)

    now = datetime.now(timezone.utc)
    item.status = OutboundStatusEnum.sent
    item.sent_at = now
    item.reviewed_at = now
    item.reviewed_by = body.reviewed_by
    db.commit()
    db.refresh(item)
    return item


@router.post("/{msg_id}/edit", response_model=OutboundQueueRead)
def edit(msg_id: uuid.UUID, body: ReviewEditRequest, db: Session = Depends(get_db)) -> OutboundQueueItem:
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    item.message = body.message
    item.status = OutboundStatusEnum.edited
    item.reviewed_at = datetime.now(timezone.utc)
    item.reviewed_by = body.reviewed_by
    db.commit()
    db.refresh(item)
    return item


@router.post("/{msg_id}/reject", response_model=OutboundQueueRead)
def reject(msg_id: uuid.UUID, body: ReviewRejectRequest, db: Session = Depends(get_db)) -> OutboundQueueItem:
    item = _get_item(db, msg_id)
    if item.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"item is already '{item.status.value}'")

    item.status = OutboundStatusEnum.rejected
    item.reviewed_at = datetime.now(timezone.utc)
    item.reviewed_by = body.reviewed_by
    db.commit()
    db.refresh(item)
    return item
