from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.commitment import Commitment
from app.schemas.commitment import CommitmentCreate, CommitmentUpdate

async def create_commitments(
    db: AsyncSession, items: list[CommitmentCreate]
) -> list[Commitment]:
    """Single source of truth for saving commitments."""
    objs = [Commitment(**c.model_dump()) for c in items]
    db.add_all(objs)
    await db.commit()
    for o in objs:
        await db.refresh(o)
    return objs

async def list_commitments(db: AsyncSession) -> list[Commitment]:
    """Retrieve all commitments, ordered by deadline."""
    result = await db.execute(select(Commitment).order_by(Commitment.deadline))
    return list(result.scalars().all())

async def get_commitment(db: AsyncSession, commitment_id: int) -> Commitment | None:
    """Retrieve a single commitment by ID."""
    return await db.get(Commitment, commitment_id)

async def update_commitment(
    db: AsyncSession, commitment_id: int, payload: CommitmentUpdate
) -> Commitment | None:
    """Update a commitment by ID."""
    obj = await db.get(Commitment, commitment_id)
    if not obj:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.commit()
    await db.refresh(obj)
    return obj

async def delete_commitment(db: AsyncSession, commitment_id: int) -> bool:
    """Delete a commitment by ID."""
    obj = await db.get(Commitment, commitment_id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True
