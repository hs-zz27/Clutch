"""Phase 3 - the tool registry the agent can call.

Each tool is a thin async wrapper over an existing service. We expose them to
Gemini as function declarations; the model decides which to call and in what
order. Everything returned here must be JSON-serializable (datetimes -> ISO
strings) so it can be handed back to the model as a function response.
"""
from __future__ import annotations

import datetime
from typing import Any

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import commitments as commitments_service
from app.services import planner as planner_service
from app.services import triage as triage_service


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


async def get_commitments(db: AsyncSession) -> dict:
    rows = await commitments_service.list_commitments(db)
    return {
        "commitments": [
            {
                "id": c.id,
                "title": c.title,
                "deadline": c.deadline.isoformat(),
                "importance": c.importance,
                "status": c.status.value,
                "progress_pct": c.progress_pct,
                "est_effort_minutes": c.est_effort_minutes,
                "stakeholder": c.stakeholder,
                "min_viable_definition": c.min_viable_definition,
            }
            for c in rows
        ]
    }


async def run_plan(db: AsyncSession) -> dict:
    rows = await commitments_service.list_commitments(db)
    return _jsonable(planner_service.build_plan(list(rows), _now()))


async def run_triage(db: AsyncSession) -> dict:
    rows = await commitments_service.list_commitments(db)
    return _jsonable(triage_service.run_triage(list(rows), _now()))


# dispatch table: tool name -> coroutine(db)
TOOLS = {
    "get_commitments": get_commitments,
    "run_plan": run_plan,
    "run_triage": run_triage,
}

# what we advertise to Gemini
FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_commitments",
        description=(
            "List all of the user's commitments with their deadlines, importance, "
            "status and progress. Call this first to see the raw situation."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="run_plan",
        description=(
            "Run the reverse-clock planner. Returns each task's projected finish, "
            "latest_start, lateness, risk label, and the total time deficit. Use it "
            "to find out whether the user is in trouble and by how much."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="run_triage",
        description=(
            "Run the triage/salvage engine. Returns a DO_FULLY / DO_MINIMALLY / "
            "DEFER / DROP decision with a reason for each commitment, plus capacity, "
            "required and deficit minutes. Use it when run_plan shows a deficit and "
            "you need to decide what to sacrifice."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
]


async def dispatch(name: str, db: AsyncSession) -> dict:
    tool = TOOLS.get(name)
    if tool is None:
        return {"error": f"unknown tool: {name}"}
    return await tool(db)
