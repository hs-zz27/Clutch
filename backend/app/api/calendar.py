from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.calendar import BusyBlockCreate, BusyBlockRead, CapacityRead
from app.services import busy_blocks as busy_service
from app.services import capacity as capacity_service
from app.services import commitments as commitments_service
from app.services import ics as ics_service
from app.services import triage as triage_service

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/busy", response_model=BusyBlockRead)
async def create_busy_block(
    payload: BusyBlockCreate, db: AsyncSession = Depends(get_db)
):
    return await busy_service.create_block(
        db, start=payload.start, end=payload.end, label=payload.label
    )


@router.get("/busy", response_model=list[BusyBlockRead])
async def list_busy_blocks(db: AsyncSession = Depends(get_db)):
    return await busy_service.list_blocks(db)


@router.delete("/busy/{block_id}", status_code=204)
async def delete_busy_block(block_id: int, db: AsyncSession = Depends(get_db)):
    block = await busy_service.get_block(db, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Busy block not found")
    await busy_service.delete_block(db, block)


@router.post("/sync-ics")
async def sync_ics(db: AsyncSession = Depends(get_db)):
    """Import busy blocks from the configured ICS feed (optional feature)."""
    try:
        return await ics_service.sync(db)
    except ics_service.IcsNotAvailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=502, detail="Could not fetch or parse the ICS feed."
        )


@router.get("/capacity", response_model=CapacityRead)
async def get_capacity(
    until: datetime | None = Query(
        default=None,
        description="Compute capacity until this time; defaults to the latest commitment deadline.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Preview the realistic focus minutes available between now and a horizon."""
    now = datetime.now(timezone.utc)

    if until is None:
        rows = list(await commitments_service.list_commitments(db))
        pending = triage_service.pending_commitments(rows)
        if not pending:
            raise HTTPException(
                status_code=400,
                detail="No pending commitments; pass an explicit 'until' time.",
            )
        until = max(c.deadline for c in pending)

    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    if until <= now:
        raise HTTPException(status_code=400, detail="'until' must be in the future.")

    blocks = await busy_service.list_blocks_between(db, now, until)
    minutes = capacity_service.available_minutes(
        now,
        until,
        [(b.start, b.end) for b in blocks],
        capacity_service.policy_from_settings(),
    )
    return CapacityRead(
        from_time=now,
        until=until,
        available_minutes=round(minutes, 1),
        available_hours=round(minutes / 60.0, 2),
    )
