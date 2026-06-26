"""Explainable decision ledger endpoints (feature #9).

GET /ledger            -> a page of state-changing actions, newest first
POST /ledger/{id}/undo -> reverse a reversible action
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.ledger import LedgerEntryRead
from app.services import ledger as ledger_service

router = APIRouter(prefix="/ledger", tags=["ledger"])

class LedgerPage(BaseModel):
    items: list[LedgerEntryRead]
    total: int
    limit: int
    offset: int

@router.get("", response_model=LedgerPage)
async def list_ledger(
    limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)
):
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    items = await ledger_service.list_entries(db, limit=limit, offset=offset)
    total = await ledger_service.count_entries(db)
    return LedgerPage(
        items=[LedgerEntryRead.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    )

@router.post("/{entry_id}/undo")
async def undo_ledger_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await ledger_service.undo(db, entry_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "cannot undo"))
    return result
