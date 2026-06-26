"""Phase 3 - the tool registry the agent can call.

Each tool is a thin async wrapper over an existing service. We expose them to
Gemini as function declarations; the model decides which to call and in what
order. Everything returned here must be JSON-serializable (datetimes -> ISO
strings) so it can be handed back to the model as a function response.

Every tool has the uniform signature `async def tool(db, args)` so the dispatch
loop can call them generically; tools that take no parameters simply ignore
`args`.
"""
from __future__ import annotations

import datetime
from typing import Any

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import busy_blocks as busy_service
from app.services import calibration as calibration_service
from app.services import capacity as capacity_service
from app.services import commitments as commitments_service
from app.services import knowledge as knowledge_service
from app.services import outbox as outbox_service
from app.services import planner as planner_service
from app.services import renegotiation as renegotiation_service
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


async def get_commitments(db: AsyncSession, args: dict) -> dict:
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
                "est_effort_p80_minutes": c.effort_p80_minutes,
                "depends_on_id": c.depends_on_id,
                "stakeholder": c.stakeholder,
                "min_viable_definition": c.min_viable_definition,
            }
            for c in rows
        ]
    }


async def run_plan(db: AsyncSession, args: dict) -> dict:
    rows = await commitments_service.list_commitments(db)
    calib = await calibration_service.get_calibration(db)
    blocks = await busy_service.list_blocks(db)
    return _jsonable(
        planner_service.build_plan(
            list(rows),
            _now(),
            calibration_factor=calib["effective_factor"],
            busy_blocks=[(b.start, b.end) for b in blocks],
            policy=capacity_service.policy_from_settings(),
        )
    )


async def _real_capacity(
    db: AsyncSession, pending: list, now: datetime.datetime
) -> float | None:
    """Realistic focus minutes from now to the last deadline, or None."""
    if not pending:
        return None
    horizon = max(c.deadline for c in pending)
    blocks = await busy_service.list_blocks_between(db, now, horizon)
    return capacity_service.available_minutes(
        now,
        horizon,
        [(b.start, b.end) for b in blocks],
        capacity_service.policy_from_settings(),
    )


async def run_triage(db: AsyncSession, args: dict) -> dict:
    rows = list(await commitments_service.list_commitments(db))
    now = _now()
    pending = triage_service.pending_commitments(rows)
    capacity = await _real_capacity(db, pending, now)
    calib = await calibration_service.get_calibration(db)
    blocks = await busy_service.list_blocks(db)
    return _jsonable(
        triage_service.run_triage(
            rows,
            now,
            capacity_minutes=capacity,
            calibration_factor=calib["effective_factor"],
            busy_blocks=[(b.start, b.end) for b in blocks],
            policy=capacity_service.policy_from_settings(),
        )
    )


async def search_knowledge(db: AsyncSession, args: dict) -> dict:
    query = (args or {}).get("query", "").strip()
    if not query:
        return {"error": "query is required"}
    return await knowledge_service.search(query)


async def draft_renegotiation(db: AsyncSession, args: dict) -> dict:
    """Draft (never send) a renegotiation message for a commitment."""
    raw_id = (args or {}).get("commitment_id")
    if raw_id is None:
        return {"error": "commitment_id is required"}
    try:
        commitment_id = int(raw_id)
    except (TypeError, ValueError):
        return {"error": "commitment_id must be an integer"}

    commitment = await commitments_service.get_commitment(db, commitment_id)
    if commitment is None:
        return {"error": f"no commitment with id {commitment_id}"}

    tone = (args or {}).get("tone") or "professional and apologetic"
    try:
        drafted = await renegotiation_service.draft_message(commitment, tone)
    except Exception:
        return {"error": "failed to generate the renegotiation draft"}

    msg = await outbox_service.create_draft(
        db,
        commitment_id=commitment.id,
        subject=drafted["subject"],
        body=drafted["body"],
        recipient=commitment.stakeholder,
    )
    return {
        "id": msg.id,
        "commitment_id": msg.commitment_id,
        "recipient": msg.recipient,
        "subject": msg.subject,
        "body": msg.body,
        "status": msg.status.value,
        "note": "Draft saved to the outbox. A human must review and send it.",
    }


# dispatch table: tool name -> coroutine(db, args)
TOOLS = {
    "get_commitments": get_commitments,
    "run_plan": run_plan,
    "run_triage": run_triage,
    "search_knowledge": search_knowledge,
    "draft_renegotiation": draft_renegotiation,
}

# what we advertise to Gemini
FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_commitments",
        description=(
            "List all of the user's commitments with their deadlines, importance, "
            "status, progress, expected/worst-case effort and any prerequisite "
            "(depends_on_id). Call this first to see the raw situation."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="run_plan",
        description=(
            "Run the reverse-clock critical-path planner. Returns each task's "
            "projected finish (expected and worst-case), latest_start, lateness, "
            "risk label, plus the total deficit as a range and a make_probability. "
            "Respects task dependencies. Use it to find out whether the user is in "
            "trouble and by how much."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="run_triage",
        description=(
            "Run the triage/salvage engine. Returns a DO_FULLY / DO_MINIMALLY / "
            "DEFER / DROP decision with a reason for each commitment, plus capacity, "
            "required and deficit minutes. Capacity reflects the user's REAL focus "
            "time (work hours minus calendar busy blocks). Use it when run_plan "
            "shows a deficit and you need to decide what to sacrifice."
        ),
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="search_knowledge",
        description=(
            "Search the user's uploaded documents (assignment briefs, specs, "
            "rubrics, emails) to ground a decision - for example to learn what "
            "'done' really means for a deliverable or to scope a minimum-viable "
            "version. Pass a natural-language query."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(
                    type=types.Type.STRING,
                    description="What to look up in the uploaded documents.",
                )
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="draft_renegotiation",
        description=(
            "Draft a message asking a stakeholder to extend the deadline or reduce "
            "the scope of a commitment. Use this for items you decided to DEFER, or "
            "any task whose deadline is no longer realistic. This only SAVES a "
            "draft for the user to review and send - it never sends anything "
            "itself."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "commitment_id": types.Schema(
                    type=types.Type.INTEGER,
                    description="The id of the commitment to renegotiate.",
                ),
                "tone": types.Schema(
                    type=types.Type.STRING,
                    description="Optional desired tone, e.g. 'professional and apologetic'.",
                ),
            },
            required=["commitment_id"],
        ),
    ),
]


async def dispatch(name: str, db: AsyncSession, args: dict) -> dict:
    tool = TOOLS.get(name)
    if tool is None:
        return {"error": f"unknown tool: {name}"}
    return await tool(db, args)
