"""Persistence for busy blocks (unavailable time spans)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.busy_block import BusyBlock, BusySource


async def create_block(
    db: AsyncSession,
    *,
    user_id: int,
    start: datetime,
    end: datetime,
    label: str | None = None,
    source: BusySource = BusySource.manual,
    external_uid: str | None = None,
) -> BusyBlock:
    block = BusyBlock(
        user_id=user_id,
        start=start,
        end=end,
        label=label,
        source=source,
        external_uid=external_uid,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def list_blocks(db: AsyncSession, user_id: int) -> list[BusyBlock]:
    stmt = select(BusyBlock).where(BusyBlock.user_id == user_id).order_by(BusyBlock.start.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_blocks_between(
    db: AsyncSession, user_id: int, start: datetime, end: datetime
) -> list[BusyBlock]:
    """Blocks overlapping [start, end). Index on `start` keeps this cheap."""
    stmt = (
        select(BusyBlock)
        .where(BusyBlock.user_id == user_id, BusyBlock.end > start, BusyBlock.start < end)
        .order_by(BusyBlock.start.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_block(db: AsyncSession, block_id: int, user_id: int) -> BusyBlock | None:
    result = await db.execute(select(BusyBlock).where(BusyBlock.id == block_id, BusyBlock.user_id == user_id))
    return result.scalars().first()


async def delete_block(db: AsyncSession, block: BusyBlock) -> None:
    await db.delete(block)
    await db.commit()


async def replace_ics_blocks(
    db: AsyncSession,
    user_id: int,
    blocks: list[dict],
) -> int:
    """Atomically swap all ICS-sourced blocks for a freshly imported set.

    Each dict has keys: start, end, label, external_uid. Manual blocks are
    untouched. Returns the number of blocks inserted.
    """
    await db.execute(delete(BusyBlock).where(BusyBlock.user_id == user_id, BusyBlock.source == BusySource.ics))
    for b in blocks:
        db.add(
            BusyBlock(
                user_id=user_id,
                start=b["start"],
                end=b["end"],
                label=b.get("label"),
                source=BusySource.ics,
                external_uid=b.get("external_uid"),
            )
        )
    await db.commit()
    return len(blocks)
