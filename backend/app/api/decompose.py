"""Task decomposition endpoint (feature #5).

POST /commitments/{id}/decompose { persist?: bool }
  -> { commitment_id, persisted, subtasks, created_ids }

When persist is true the suggested subtasks are created as a dependency chain
(subtask N depends on subtask N-1) inheriting the parent's deadline, importance
and stakeholder, and each creation is recorded in the decision ledger.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.commitment import CommitmentCreate
from app.schemas.decompose import DecomposeBody
from app.services import commitments as commitments_service
from app.services import decompose as decompose_service
from app.services import ledger as ledger_service

router = APIRouter(prefix="/commitments", tags=["decompose"])


@router.post("/{commitment_id}/decompose")
async def decompose_commitment(
    commitment_id: int,
    body: DecomposeBody | None = None,
    db: AsyncSession = Depends(get_db),
):
    parent = await commitments_service.get_commitment(db, commitment_id)
    if parent is None:
        raise HTTPException(404, "Commitment not found")

    try:
        suggestions = await decompose_service.suggest_subtasks(parent)
    except Exception:
        raise HTTPException(502, "Failed to generate a decomposition")

    persist = bool(body and body.persist)
    created = []
    if persist and suggestions:
        prev_id: int | None = None
        for s in suggestions:
            payload = CommitmentCreate(
                title=s.title,
                deadline=parent.deadline,
                est_effort_minutes=s.est_effort_minutes,
                effort_p80_minutes=s.effort_p80_minutes,
                importance=parent.importance,
                stakeholder=parent.stakeholder,
                depends_on_id=prev_id,
            )
            objs = await commitments_service.create_commitments(db, [payload])
            obj = objs[0]
            prev_id = obj.id
            await ledger_service.record(
                db,
                action="create_commitment",
                target_type="commitment",
                target_id=obj.id,
                summary=f"Subtask of '{parent.title}': {obj.title}",
                reasoning=f"Auto-decomposed from commitment #{parent.id}.",
                reversible=True,
                commit=False,
            )
            created.append(obj)
        await db.commit()
        for o in created:
            await db.refresh(o)

    return {
        "commitment_id": parent.id,
        "persisted": persist,
        "subtasks": [s.model_dump() for s in suggestions],
        "created_ids": [o.id for o in created],
    }
