from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.db import get_db
from app.models.commitment import Commitment
from app.services import planner as planner_service
from app.services import calibration as calibration_service
from app.services import busy_blocks as busy_service
from app.services import capacity as capacity_service

router = APIRouter(prefix="/plan", tags=["planner"])

@router.get("")
async def get_plan(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Commitment))
    commitments = list(result.scalars().all())
    calibration = await calibration_service.get_calibration(db)
    blocks = await busy_service.list_blocks(db)
    plan = planner_service.build_plan(
        commitments,
        datetime.now(timezone.utc),
        calibration_factor=calibration["effective_factor"],
        busy_blocks=[(b.start, b.end) for b in blocks],
        policy=capacity_service.policy_from_settings(),
    )
    plan["calibration"] = calibration
    return plan
