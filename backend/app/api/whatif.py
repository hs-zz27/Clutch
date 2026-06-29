"""What-if simulation endpoint (feature #6).

POST /whatif { scenario } -> { baseline, scenario, diff }. Read-only: it never
mutates the database. Uses the same real working-time planner as GET /plan (work
hours minus calendar busy blocks) and the same learned calibration factor, so
the baseline deficit matches the War Room timeline instead of always reading 0.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.whatif import WhatIfScenario
from app.services import busy_blocks as busy_service
from app.services import calibration as calibration_service
from app.services import capacity as capacity_service
from app.services import commitments as commitments_service
from app.services import triage as triage_service
from app.services import whatif as whatif_service

router = APIRouter(prefix="/whatif", tags=["whatif"])

def _real_capacity(busy: list, pending: list, now: datetime) -> float | None:
    if not pending:
        return None
    horizon = max(c.deadline for c in pending)
    return capacity_service.available_minutes(
        now,
        horizon,
        [(b.start, b.end) for b in busy],
        capacity_service.policy_from_settings(),
    )

@router.post("")
async def run_whatif(
    scenario: WhatIfScenario, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    rows = list(await commitments_service.list_commitments(db, user.id))
    now = datetime.now(timezone.utc)
    pending = triage_service.pending_commitments(rows)
    blocks = await busy_service.list_blocks(db, user.id)
    capacity = _real_capacity(blocks, pending, now)
    calib = await calibration_service.get_calibration(db, user.id)
    return whatif_service.simulate(
        rows,
        now,
        scenario,
        busy_blocks=[(b.start, b.end) for b in blocks],
        policy=capacity_service.policy_from_settings(),
        base_capacity_minutes=capacity,
        calibration_factor=calib["effective_factor"],
    )
