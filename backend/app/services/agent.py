"""Phase 3 - the agent core: a Gemini function-calling ReAct loop.

Give it a goal (e.g. \"I'm out of time, help\"). It reasons, decides which tool
to call, observes the result, and loops until it can give a final answer. We
keep a visible trace of every step - that trace is the evidence of real agency
(and it's what we render in the War Room UI later).
"""
from __future__ import annotations

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.gemini import client, GeminiUnavailable
from app.services import agent_tools

MODEL = "gemini-2.5-flash"
MAX_STEPS = 8

SYSTEM_PROMPT = """You are Clutch, a calm, decisive crisis chief-of-staff for someone who is out of time.
Your job: assess the situation with your tools, then tell the user exactly what to do to survive their deadlines.

How to work:
1. Call get_commitments to see the raw situation.
2. Call run_plan to find out if there is a time deficit and how bad it is.
3. If there is a deficit, call run_triage to decide what to sacrifice.
4. When you need to know what a deliverable actually requires, or how small a
   minimum-viable version can be, call search_knowledge to consult the user's
   uploaded briefs and specs before committing to a recommendation.
5. For any commitment you decide to DEFER (or whose deadline is no longer
   realistic), call draft_renegotiation to prepare a message to its stakeholder.
   This only saves a draft - you must NEVER claim a message was sent. Tell the
   user a draft is ready for them to review and send.
6. Then STOP calling tools and write a short, direct survival plan in plain language:
   - lead with the headline (are they in deficit, and by how much).
   - list what to DO FULLY, DO MINIMALLY, DEFER, and DROP - each with its one-line reason.
   - note any renegotiation drafts you prepared.
   - end with the single most urgent next action.

Be honest and decisive. Never invent commitments or numbers - only use what the tools return.

Write the final answer for a stressed, non-technical person. Rules:
- No jargon. Never say "deficit", "capacity", "p80", "calibration factor", or "feasible".
  Instead say things like "you're behind by about 2 hours", "free time", "worst case",
  "you're on track".
- Start with the bottom line in ONE short sentence (e.g. "Good news - you've got enough time.").
- Then a short bulleted list of what to do, most urgent first. Use "- " bullets and **bold**
  only on the task name; the app renders Markdown.
- Keep it under ~120 words. Warm, direct, encouraging. No ALL-CAPS labels like "VERDICT".
"""


async def run_agent(db: AsyncSession, goal: str) -> dict:
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[types.Tool(function_declarations=agent_tools.FUNCTION_DECLARATIONS)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=goal)])
    ]
    trace: list[dict] = []

    for _ in range(MAX_STEPS):
        try:
            resp = await client.aio.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
        except GeminiUnavailable as e:
            raise HTTPException(status_code=503, detail=str(e))
        if not resp.candidates or resp.candidates[0].content is None:
            return {
                "final_message": (
                    "I couldn't finish the triage just now - the model returned "
                    "no usable response. Please try again."
                ),
                "trace": trace,
            }
        candidate = resp.candidates[0]
        contents.append(candidate.content)

        calls = resp.function_calls
        if not calls:
            return {"final_message": resp.text or "", "trace": trace}

        for fc in calls:
            args = dict(fc.args or {})
            trace.append({"type": "tool_call", "tool": fc.name, "args": args})
            result = await agent_tools.dispatch(fc.name, db, args)
            trace.append({"type": "tool_result", "tool": fc.name, "result": result})
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=fc.name, response={"result": result}
                        )
                    ],
                )
            )

    return {
        "final_message": "Reached the step limit before finishing. Partial trace returned.",
        "trace": trace,
    }
