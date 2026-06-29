"""Estimate calibration endpoint (feature #4).

GET /calibration -> { factor, sample_size, applied, effective_factor, tendency }

The learned factor is also applied by /plan; this endpoint lets the UI explain
how Clutch has adjusted to the user's real pace.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services import calibration as calibration_service

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.get("")
async def get_calibration(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await calibration_service.get_calibration(db, user.id)
