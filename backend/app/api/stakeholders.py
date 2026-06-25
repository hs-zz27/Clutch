"""Stakeholder directory endpoints (feature #8)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.stakeholder import (
    StakeholderCreate,
    StakeholderRead,
    StakeholderUpdate,
)
from app.services import stakeholders as service

router = APIRouter(prefix="/stakeholders", tags=["stakeholders"])


@router.post("", response_model=StakeholderRead)
async def create_stakeholder(
    payload: StakeholderCreate, db: AsyncSession = Depends(get_db)
):
    try:
        return await service.create_stakeholder(db, payload)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, f"A stakeholder named '{payload.name}' already exists")


@router.get("", response_model=list[StakeholderRead])
async def list_stakeholders(db: AsyncSession = Depends(get_db)):
    return await service.list_stakeholders(db)


@router.get("/{stakeholder_id}", response_model=StakeholderRead)
async def get_stakeholder(stakeholder_id: int, db: AsyncSession = Depends(get_db)):
    obj = await service.get_stakeholder(db, stakeholder_id)
    if obj is None:
        raise HTTPException(404, "Stakeholder not found")
    return obj


@router.patch("/{stakeholder_id}", response_model=StakeholderRead)
async def update_stakeholder(
    stakeholder_id: int,
    payload: StakeholderUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        obj = await service.update_stakeholder(db, stakeholder_id, payload)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Another stakeholder already has that name")
    if obj is None:
        raise HTTPException(404, "Stakeholder not found")
    return obj


@router.delete("/{stakeholder_id}", status_code=204)
async def delete_stakeholder(stakeholder_id: int, db: AsyncSession = Depends(get_db)):
    ok = await service.delete_stakeholder(db, stakeholder_id)
    if not ok:
        raise HTTPException(404, "Stakeholder not found")
