from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from pydantic import BaseModel

from app.core.db import get_db
from app.schemas.commitment import CommitmentCreate, CommitmentUpdate, CommitmentRead
from app.core.gemini import client
from app.services import commitments as service

class ParseRequest(BaseModel):
    text: str

router = APIRouter(prefix="/commitments", tags=["commitments"])

@router.post("", response_model=CommitmentRead)
async def create_commitment(payload: CommitmentCreate, db: AsyncSession = Depends(get_db)):
    objs = await service.create_commitments(db, [payload])
    return objs[0]

@router.get("", response_model=list[CommitmentRead])
async def list_commitments(db: AsyncSession = Depends(get_db)):
    return await service.list_commitments(db)

@router.get("/{commitment_id}", response_model=CommitmentRead)
async def get_commitment(commitment_id: int, db: AsyncSession = Depends(get_db)):
    obj = await service.get_commitment(db, commitment_id)
    if not obj:
        raise HTTPException(404, "Commitment not found")
    return obj

@router.patch("/{commitment_id}", response_model=CommitmentRead)
async def update_commitment(commitment_id: int, payload: CommitmentUpdate, db: AsyncSession = Depends(get_db)):
    obj = await service.update_commitment(db, commitment_id, payload)
    if not obj:
        raise HTTPException(404, "Commitment not found")
    return obj

@router.delete("/{commitment_id}", status_code=204)
async def delete_commitment(commitment_id: int, db: AsyncSession = Depends(get_db)):
    success = await service.delete_commitment(db, commitment_id)
    if not success:
        raise HTTPException(404, "Commitment not found")

@router.post("/parse", response_model=list[CommitmentRead])
async def parse_commitments(payload: ParseRequest, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc).isoformat()
    prompt = f"""You extract commitments/tasks from a user's messy text.
The current datetime (UTC) is {now}.
Resolve all relative dates ("Friday 5pm", "tomorrow noon") into absolute ISO 8601 datetimes.
Estimate est_effort_minutes realistically. Set importance 1-5 (5 = critical).
If a stakeholder/person is mentioned, fill it in; otherwise leave it null.
User text:
{payload.text}"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[CommitmentCreate],
        },
    )
    parsed: list[CommitmentCreate] = response.parsed
    return await service.create_commitments(db, parsed)
