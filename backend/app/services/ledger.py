"""Phase 9 feature #9 - explainable decision ledger service.

Record state-changing actions with reasoning and (where reversible) a JSON
snapshot of the prior state, and undo them. All snapshots are JSON-safe
(datetimes -> ISO strings, enums -> values) so they round-trip through the DB.
"""
from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision_ledger import DecisionLedger
from app.models.commitment import Commitment, Status

_COMMITMENT_FIELDS = (
    "title",
    "description",
    "deadline",
    "est_effort_minutes",
    "effort_p80_minutes",
    "importance",
    "stakeholder",
    "min_viable_definition",
    "depends_on_id",
    "status",
    "progress_pct",
)


def snapshot_commitment(c) -> dict:
    """JSON-safe snapshot of a commitment's editable fields."""
    snap: dict = {}
    for f in _COMMITMENT_FIELDS:
        v = getattr(c, f, None)
        if isinstance(v, datetime.datetime):
            v = v.isoformat()
        elif isinstance(v, Status):
            v = v.value
        snap[f] = v
    return snap


def _coerce_commitment(snap: dict) -> dict:
    out: dict = {}
    for f in _COMMITMENT_FIELDS:
        if f not in snap:
            continue
        v = snap[f]
        if f == "deadline" and isinstance(v, str):
            v = datetime.datetime.fromisoformat(v)
        elif f == "status" and isinstance(v, str):
            v = Status(v)
        out[f] = v
    return out


async def record(
    db: AsyncSession,
    *,
    action: str,
    target_type: str,
    summary: str,
    target_id: int | None = None,
    reasoning: str | None = None,
    payload: dict | None = None,
    reversible: bool = False,
    commit: bool = True,
) -> DecisionLedger:
    entry = DecisionLedger(
        action=action,
        target_type=target_type,
        target_id=target_id,
        summary=(summary or "")[:512],
        reasoning=reasoning,
        payload=payload or {},
        reversible=reversible,
    )
    db.add(entry)
    if commit:
        await db.commit()
        await db.refresh(entry)
    return entry


async def list_entries(db: AsyncSession, limit: int = 100) -> list[DecisionLedger]:
    result = await db.execute(
        select(DecisionLedger)
        .order_by(DecisionLedger.created_at.desc(), DecisionLedger.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def undo(db: AsyncSession, entry_id: int) -> dict:
    entry = await db.get(DecisionLedger, entry_id)
    if entry is None:
        return {"ok": False, "error": "ledger entry not found"}
    if entry.undone:
        return {"ok": False, "error": "this action was already undone"}
    if not entry.reversible:
        return {"ok": False, "error": "this action cannot be undone"}

    outcome = await _apply_undo(db, entry)
    if outcome.get("ok"):
        entry.undone = True
        await db.commit()
        await db.refresh(entry)
    else:
        await db.rollback()
    return outcome


async def _apply_undo(db: AsyncSession, entry: DecisionLedger) -> dict:
    if entry.target_type != "commitment":
        return {"ok": False, "error": "no undo handler for this action"}

    payload = entry.payload or {}

    if entry.action == "create_commitment":
        if entry.target_id is None:
            return {"ok": False, "error": "missing target"}
        obj = await db.get(Commitment, entry.target_id)
        if obj is not None:
            await db.delete(obj)
        return {"ok": True, "detail": "Removed the created commitment."}

    if entry.action == "delete_commitment":
        before = payload.get("before") or {}
        if not before:
            return {"ok": False, "error": "no snapshot to restore"}
        obj = Commitment(**_coerce_commitment(before))
        db.add(obj)
        return {"ok": True, "detail": "Recreated the deleted commitment (new id)."}

    if entry.action == "update_commitment":
        before = payload.get("before") or {}
        if entry.target_id is None:
            return {"ok": False, "error": "missing target"}
        obj = await db.get(Commitment, entry.target_id)
        if obj is None:
            return {"ok": False, "error": "commitment no longer exists"}
        for f, v in _coerce_commitment(before).items():
            setattr(obj, f, v)
        return {"ok": True, "detail": "Restored the previous values."}

    return {"ok": False, "error": "no undo handler for this action"}
