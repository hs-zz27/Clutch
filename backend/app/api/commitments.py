from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from pydantic import BaseModel
import logging

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.commitment import CommitmentCreate, CommitmentUpdate, CommitmentRead
from app.core.gemini import client, GeminiUnavailable
from app.services import commitments as service
from app.services import ledger as ledger_service

logger = logging.getLogger("clutch.commitments")

class ParseRequest(BaseModel):
    text: str

router = APIRouter(prefix="/commitments", tags=["commitments"])

@router.post("", response_model=CommitmentRead)
async def create_commitment(payload: CommitmentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    err = await service.validate_dependency(db, payload.depends_on_id, user.id)
    if err:
        raise HTTPException(400, err)
    objs = await service.create_commitments(db, [payload], user.id)
    obj = objs[0]
    await ledger_service.record(
        db,
        action="create_commitment",
        target_type="commitment",
        target_id=obj.id,
        summary=f"Created commitment '{obj.title}'",
        reasoning="Added via the commitments API.",
        reversible=True,
        user_id=user.id,
    )
    return obj

@router.get("", response_model=list[CommitmentRead])
async def list_commitments(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await service.list_commitments(db, user.id)

@router.get("/{commitment_id}", response_model=CommitmentRead)
async def get_commitment(commitment_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    obj = await service.get_commitment(db, commitment_id, user.id)
    if not obj:
        raise HTTPException(404, "Commitment not found")
    return obj

@router.patch("/{commitment_id}", response_model=CommitmentRead)
async def update_commitment(commitment_id: int, payload: CommitmentUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    existing = await service.get_commitment(db, commitment_id, user.id)
    if not existing:
        raise HTTPException(404, "Commitment not found")
    changed = list(payload.model_dump(exclude_unset=True).keys())
    if "depends_on_id" in changed:
        err = await service.validate_dependency(
            db, payload.depends_on_id, user.id, self_id=commitment_id
        )
        if err:
            raise HTTPException(400, err)
    before = ledger_service.snapshot_commitment(existing)
    obj = await service.update_commitment(db, commitment_id, user.id, payload)
    if not obj:
        raise HTTPException(404, "Commitment not found")
    await ledger_service.record(
        db,
        action="update_commitment",
        target_type="commitment",
        target_id=commitment_id,
        summary=f"Updated '{obj.title}' ({', '.join(changed) if changed else 'no fields'})",
        reasoning="Edited via the commitments API.",
        payload={"before": before, "changed": changed},
        reversible=True,
        user_id=user.id,
    )
    return obj

@router.delete("/{commitment_id}", status_code=204)
async def delete_commitment(commitment_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    existing = await service.get_commitment(db, commitment_id, user.id)
    if not existing:
        raise HTTPException(404, "Commitment not found")
    before = ledger_service.snapshot_commitment(existing)
    title = existing.title
    success = await service.delete_commitment(db, commitment_id, user.id)
    if not success:
        raise HTTPException(404, "Commitment not found")
    await ledger_service.record(
        db,
        action="delete_commitment",
        target_type="commitment",
        target_id=commitment_id,
        summary=f"Deleted '{title}'",
        reasoning="Removed via the commitments API.",
        payload={"before": before},
        reversible=True,
        user_id=user.id,
    )

@router.post("/parse", response_model=list[CommitmentRead])
async def parse_commitments(payload: ParseRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not payload.text or not payload.text.strip():
        raise HTTPException(400, "No text provided")
    now = datetime.now(timezone.utc).isoformat()
    prompt = f"""You extract commitments/tasks from a user's messy text.
The current datetime (UTC) is {now}.
Resolve all relative dates ("Friday 5pm", "tomorrow noon") into absolute ISO 8601 datetimes.
Estimate est_effort_minutes realistically. Set importance 1-5 (5 = critical).
If a stakeholder/person is mentioned, fill it in; otherwise leave it null.
User text:
{payload.text}"""
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[CommitmentCreate],
            },
        )
        parsed: list[CommitmentCreate] = list(response.parsed or [])
    except GeminiUnavailable as e:
        logger.warning("Commitment parse unavailable: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Surface the real cause instead of swallowing it into a blank 502.
        logger.exception("Commitment parse failed (model=gemini-2.5-flash)")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse commitments: {type(e).__name__}: {e}",
        )
    if not parsed:
        return []
    # Bulk capture must never set dependencies. The response schema exposes
    # depends_on_id, so the model *could* emit one; persisting an unvalidated
    # FK would raise IntegrityError -> 500. Strip it defensively.
    for item in parsed:
        item.depends_on_id = None
    created = await service.create_commitments(db, parsed, user.id)
    for obj in created:
        await ledger_service.record(
            db,
            action="create_commitment",
            target_type="commitment",
            target_id=obj.id,
            summary=f"Parsed commitment '{obj.title}' from text",
            reasoning="Extracted from natural-language input.",
            reversible=True,
            commit=False,
            user_id=user.id,
        )
    await db.commit()
    return created