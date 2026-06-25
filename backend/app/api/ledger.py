"""Explainable decision ledger endpoints (feature #9).

GET /ledger          -> recent state-changing actions, newest first
POST /ledger/{id}/undo -> reverse a reversible action
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.ledger import LedgerEntryRead
from app.services import ledger as ledger_service

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("", response_model=list[LedgerEntryRead])
async def list_ledger(limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await ledger_service.list_entries(db, limit=min(max(limit, 1), 500))


@router.post("/{entry_id}/undo")
async def undo_ledger_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await ledger_service.undo(db, entry_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "cannot undo"))
    return result
