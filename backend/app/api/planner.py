from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.db import get_db
from app.models.commitment import Commitment
from app.services import planner as planner_service

router = APIRouter(prefix="/plan", tags=["planner"])

@router.get("")
async def get_plan(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Commitment))
    commitments = result.scalars().all()
    return planner_service.build_plan(list(commitments), datetime.now(timezone.utc))
