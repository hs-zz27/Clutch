"""Persistence + state transitions for the renegotiation outbox.

Kept separate from draft *generation* (services/renegotiation.py) so the AI
layer and the storage layer stay decoupled and independently testable.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.renegotiation import OutboxStatus, RenegotiationMessage


async def create_draft(
    db: AsyncSession,
    *,
    commitment_id: int,
    subject: str,
    body: str,
    recipient: str | None = None,
) -> RenegotiationMessage:
    msg = RenegotiationMessage(
        commitment_id=commitment_id,
        subject=subject,
        body=body,
        recipient=recipient,
        status=OutboxStatus.draft,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def list_messages(
    db: AsyncSession, status: OutboxStatus | None = None
) -> list[RenegotiationMessage]:
    stmt = select(RenegotiationMessage).order_by(
        RenegotiationMessage.created_at.desc()
    )
    if status is not None:
        stmt = stmt.where(RenegotiationMessage.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_message(
    db: AsyncSession, message_id: int
) -> RenegotiationMessage | None:
    return await db.get(RenegotiationMessage, message_id)


async def update_draft(
    db: AsyncSession,
    msg: RenegotiationMessage,
    *,
    recipient: str | None = None,
    subject: str | None = None,
    body: str | None = None,
) -> RenegotiationMessage:
    if recipient is not None:
        msg.recipient = recipient
    if subject is not None:
        msg.subject = subject
    if body is not None:
        msg.body = body
    await db.commit()
    await db.refresh(msg)
    return msg


async def mark_sent(
    db: AsyncSession, msg: RenegotiationMessage
) -> RenegotiationMessage:
    msg.status = OutboxStatus.sent
    msg.sent_at = datetime.now(timezone.utc)
    msg.error = None
    await db.commit()
    await db.refresh(msg)
    return msg


async def mark_failed(
    db: AsyncSession, msg: RenegotiationMessage, error: str
) -> RenegotiationMessage:
    msg.status = OutboxStatus.failed
    msg.error = error[:1000]
    await db.commit()
    await db.refresh(msg)
    return msg
