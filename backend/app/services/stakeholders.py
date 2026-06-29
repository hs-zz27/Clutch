"""Phase 9 feature #8 - stakeholder relationship model.

CRUD over a small directory of people, plus a lookup that turns a stakeholder
name into a context dict the renegotiation drafter can use to set tone.
"""
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stakeholder import Stakeholder
from app.schemas.stakeholder import StakeholderCreate, StakeholderUpdate


async def create_stakeholder(
    db: AsyncSession, payload: StakeholderCreate, user_id: int
) -> Stakeholder:
    obj = Stakeholder(**payload.model_dump(), user_id=user_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_stakeholders(db: AsyncSession, user_id: int) -> list[Stakeholder]:
    result = await db.execute(
        select(Stakeholder).where(Stakeholder.user_id == user_id).order_by(Stakeholder.name)
    )
    return list(result.scalars().all())


async def get_stakeholder(db: AsyncSession, stakeholder_id: int, user_id: int) -> Stakeholder | None:
    result = await db.execute(select(Stakeholder).where(Stakeholder.id == stakeholder_id, Stakeholder.user_id == user_id))
    return result.scalars().first()


async def get_by_name(db: AsyncSession, name: str | None, user_id: int) -> Stakeholder | None:
    if not name or not name.strip():
        return None
    result = await db.execute(
        select(Stakeholder).where(
            func.lower(Stakeholder.name) == name.strip().lower(),
            Stakeholder.user_id == user_id
        )
    )
    return result.scalars().first()


async def update_stakeholder(
    db: AsyncSession, stakeholder_id: int, user_id: int, payload: StakeholderUpdate
) -> Stakeholder | None:
    obj = await get_stakeholder(db, stakeholder_id, user_id)
    if obj is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_stakeholder(db: AsyncSession, stakeholder_id: int, user_id: int) -> bool:
    obj = await get_stakeholder(db, stakeholder_id, user_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.commit()
    return True


async def get_context_by_name(db: AsyncSession, name: str | None, user_id: int) -> dict | None:
    """Return a tone-context dict for a stakeholder name, or None if unknown."""
    obj = await get_by_name(db, name, user_id)
    if obj is None:
        return None
    return {
        "name": obj.name,
        "relationship": obj.relationship,
        "formality": obj.formality,
        "notes": obj.notes,
    }
