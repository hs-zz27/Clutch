"""Phase 3 - the agent core: a Gemini function-calling ReAct loop.

Give it a goal (e.g. \"I'm out of time, help\"). It reasons, decides which tool
to call, observes the result, and loops until it can give a final answer. We
keep a visible trace of every step - that trace is the evidence of real agency
(and it's what we render in the War Room UI later).
"""
from __future__ import annotations

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini import client
from app.services import agent_tools

MODEL = "gemini-2.5-flash"
MAX_STEPS = 8

SYSTEM_PROMPT = """You are Clutch, a calm, decisive crisis chief-of-staff for someone who is out of time.
Your job: assess the situation with your tools, then tell the user exactly what to do to survive their deadlines.

How to work:
1. Call get_commitments to see the raw situation.
2. Call run_plan to find out if there is a time deficit and how bad it is.
3. If there is a deficit, call run_triage to decide what to sacrifice.
4. Then STOP calling tools and write a short, direct survival plan in plain language:
   - lead with the headline (are they in deficit, and by how much).
   - list what to DO FULLY, DO MINIMALLY, DEFER, and DROP - each with its one-line reason.
   - end with the single most urgent next action.

Be honest and decisive. Never invent commitments or numbers - only use what the tools return."""


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
        resp = await client.aio.models.generate_content(
            model=MODEL, contents=contents, config=config
        )
        candidate = resp.candidates[0]
        contents.append(candidate.content)

        calls = resp.function_calls
        if not calls:
            return {"final_message": resp.text or "", "trace": trace}

        for fc in calls:
            trace.append({"type": "tool_call", "tool": fc.name, "args": dict(fc.args or {})})
            result = await agent_tools.dispatch(fc.name, db)
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
