from datetime import timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.commitment import Commitment
from app.schemas.commitment import CommitmentCreate, CommitmentUpdate


def _normalize_deadline(obj: Commitment) -> None:
    """Coerce a naive deadline to UTC.

    The planner/triage compare deadlines against a tz-aware 'now'; mixing naive
    and aware datetimes raises TypeError. Gemini-extracted deadlines occasionally
    arrive without an offset, so we normalize here - the one place every
    commitment is saved.
    """
    if obj.deadline is not None and obj.deadline.tzinfo is None:
        obj.deadline = obj.deadline.replace(tzinfo=timezone.utc)


async def create_commitments(
    db: AsyncSession, items: list[CommitmentCreate], user_id: int
) -> list[Commitment]:
    """Single source of truth for saving commitments."""
    objs = [Commitment(**c.model_dump(), user_id=user_id) for c in items]
    for o in objs:
        _normalize_deadline(o)
    db.add_all(objs)
    await db.commit()
    for o in objs:
        await db.refresh(o)
    return objs

async def list_commitments(db: AsyncSession, user_id: int) -> list[Commitment]:
    """Retrieve all commitments, ordered by deadline."""
    result = await db.execute(
        select(Commitment)
        .where(Commitment.user_id == user_id)
        .order_by(Commitment.deadline)
    )
    return list(result.scalars().all())

async def get_commitment(db: AsyncSession, commitment_id: int, user_id: int) -> Commitment | None:
    """Retrieve a single commitment by ID."""
    result = await db.execute(
        select(Commitment).where(Commitment.id == commitment_id, Commitment.user_id == user_id)
    )
    return result.scalars().first()

async def update_commitment(
    db: AsyncSession, commitment_id: int, user_id: int, payload: CommitmentUpdate
) -> Commitment | None:
    """Update a commitment by ID."""
    obj = await get_commitment(db, commitment_id, user_id)
    if not obj:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    _normalize_deadline(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def delete_commitment(db: AsyncSession, commitment_id: int, user_id: int) -> bool:
    """Delete a commitment by ID."""
    obj = await get_commitment(db, commitment_id, user_id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True


async def validate_dependency(
    db: AsyncSession, depends_on_id: int | None, user_id: int, *, self_id: int | None = None
) -> str | None:
    """Return a human-readable error if depends_on_id is invalid, else None.

    Guards against self-reference, dangling references, and dependency cycles so
    the critical-path planner always receives a well-formed DAG.
    """
    if depends_on_id is None:
        return None
    if self_id is not None and depends_on_id == self_id:
        return "A commitment cannot depend on itself."
    target = await get_commitment(db, depends_on_id, user_id)
    if target is None:
        return f"Dependency #{depends_on_id} does not exist."
    # walk up the chain from the target; revisiting a node (including self) means
    # adding this edge would close a cycle.
    seen: set[int] = set()
    if self_id is not None:
        seen.add(self_id)
    cur: Commitment | None = target
    while cur is not None:
        if cur.id in seen:
            return "That dependency would create a cycle."
        seen.add(cur.id)
        if cur.depends_on_id is None:
            break
        cur = await get_commitment(db, cur.depends_on_id, user_id)
    return None
