"""Phase 9 feature #5 - automatic task decomposition.

Ask Gemini to break a single commitment into concrete, ordered subtasks with
effort estimates. Generation only - persistence (as dependency-chained
commitments) happens in the API layer so this stays a pure, testable function.
"""
from __future__ import annotations

from app.core.gemini import client
from app.models.commitment import Commitment
from app.schemas.decompose import SubtaskSuggestion

MODEL = "gemini-2.5-flash"

_PROMPT = """Break the following task into 3-7 concrete, ordered subtasks that together complete it.
Rules:
- Each subtask must be independently doable in roughly one sitting.
- Return them in execution order (the first subtask should be done first).
- Estimate est_effort_minutes as the realistic expected time, and
  effort_p80_minutes as a pessimistic worst case (>= the expected value).
- Do not invent scope beyond what the task implies.

Task: {title}
Description: {description}
Total expected effort (minutes): {effort}
Definition of done / minimum viable: {mvd}"""


async def suggest_subtasks(commitment: Commitment) -> list[SubtaskSuggestion]:
    prompt = _PROMPT.format(
        title=commitment.title,
        description=commitment.description or "n/a",
        effort=commitment.est_effort_minutes,
        mvd=commitment.min_viable_definition or "not specified",
    )
    resp = await client.aio.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[SubtaskSuggestion],
        },
    )
    return list(resp.parsed or [])
