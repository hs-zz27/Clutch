"""What-if simulation endpoint (feature #6).

POST /whatif { scenario } -> { baseline, scenario, diff }. Read-only: it never
mutates the database. Capacity uses the same real focus-time computation as the
agent (work hours minus calendar busy blocks), with the scenario's extra focus
minutes layered on top.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.db import get_db
from app.schemas.whatif import WhatIfScenario
from app.services import busy_blocks as busy_service
from app.services import capacity as capacity_service
from app.services import commitments as commitments_service
from app.services import triage as triage_service
from app.services import whatif as whatif_service

router = APIRouter(prefix="/whatif", tags=["whatif"])


async def _real_capacity(db: AsyncSession, pending: list, now: datetime) -> float | None:
    if not pending:
        return None
    horizon = max(c.deadline for c in pending)
    blocks = await busy_service.list_blocks_between(db, now, horizon)
    return capacity_service.available_minutes(
        now,
        horizon,
        [(b.start, b.end) for b in blocks],
        capacity_service.policy_from_settings(),
    )


@router.post("")
async def run_whatif(
    scenario: WhatIfScenario, db: AsyncSession = Depends(get_db)
):
    rows = list(await commitments_service.list_commitments(db))
    now = datetime.now(timezone.utc)
    pending = triage_service.pending_commitments(rows)
    capacity = await _real_capacity(db, pending, now)
    return whatif_service.simulate(rows, now, scenario, capacity)
