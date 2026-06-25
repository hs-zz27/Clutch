"""The Clutch voice agent: a Gemini Live worker for hands-free crisis triage.

Run it from the backend/ directory:
    python -m voice.agent download-files   # one-time: Silero VAD weights
    python -m voice.agent dev               # local dev (hot reload)
    python -m voice.agent start             # production

It auto-joins any LiveKit room a participant connects to (no explicit dispatch
needed), greets the user, and answers \"what do I do right now?\" by calling the
same Clutch API the web app uses.
"""
from __future__ import annotations

import logging

from livekit import agents
from livekit.agents import Agent, AgentSession, RunContext, function_tool
from livekit.plugins import google, silero

from . import config, tools
from .clutch_client import ClutchClient

logger = logging.getLogger("clutch.voice")

INSTRUCTIONS = """You are Clutch, a calm, decisive crisis chief-of-staff speaking out loud to someone who is running out of time.

You are on a live voice call, so:
- Keep replies short and spoken-friendly. No markdown, no bullet symbols, no emoji - just natural sentences.
- Lead with the single most important thing, then at most three quick follow-ups.
- Round numbers and make them human (\"about two hours\", not \"118 minutes\").

How to help:
1. When the user asks what to do, or sounds panicked, call assess_situation - it runs the full Clutch triage loop (plan plus sacrifice decisions) and returns a ready survival plan. Summarize it out loud.
2. Use get_commitments, get_plan, or get_capacity for specific questions where you do not need the full loop.
3. Use consult_notes to check what a deliverable actually requires before advising on a minimal version.
4. For anything the user wants to push back or extend, call draft_renegotiation. It only PREPARES a draft - never say a message was sent; say a draft is ready for them to review and send.

Be honest and decisive. Never invent commitments, numbers, or deadlines - only use what the tools return. If a tool fails, say so plainly and suggest checking the Clutch web app."""


class ClutchVoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)
        self._clutch = ClutchClient()

    @function_tool()
    async def assess_situation(
        self,
        context: RunContext,
        goal: str = "I'm running out of time. Tell me what to do right now.",
    ) -> dict:
        """Run the full Clutch triage loop and return a survival plan to read aloud."""
        try:
            result = await self._clutch.run_agent(goal)
        except Exception as exc:
            logger.exception("assess_situation failed")
            return {
                "error": "Could not reach the Clutch planner.",
                "detail": str(exc),
            }
        return {
            "final_message": result.get("final_message", ""),
            "reasoning_steps": len(result.get("trace", [])),
        }

    @function_tool()
    async def get_commitments(self, context: RunContext) -> dict:
        """List the user's active commitments and their status."""
        try:
            rows = await self._clutch.list_commitments()
        except Exception as exc:
            return {"error": "Could not load commitments.", "detail": str(exc)}
        return tools.summarize_commitments(rows)

    @function_tool()
    async def get_plan(self, context: RunContext) -> dict:
        """Get the reverse-clock plan: feasibility, deficit, and at-risk items."""
        try:
            plan = await self._clutch.plan()
        except Exception as exc:
            return {"error": "Could not build the plan.", "detail": str(exc)}
        return tools.summarize_plan(plan)

    @function_tool()
    async def get_capacity(self, context: RunContext) -> dict:
        """Get how much real focus time is available before the deadlines."""
        try:
            cap = await self._clutch.capacity()
        except Exception as exc:
            return {"error": "Could not compute capacity.", "detail": str(exc)}
        return tools.summarize_capacity(cap)

    @function_tool()
    async def consult_notes(self, context: RunContext, query: str) -> dict:
        """Search the user's uploaded briefs/specs for what a deliverable requires."""
        try:
            return await self._clutch.search_knowledge(query)
        except Exception as exc:
            return {"error": "Could not search your notes.", "detail": str(exc)}

    @function_tool()
    async def draft_renegotiation(
        self, context: RunContext, commitment_id: int, tone: str | None = None
    ) -> dict:
        """Prepare (never send) a renegotiation message for a commitment."""
        try:
            msg = await self._clutch.draft_renegotiation(commitment_id, tone)
        except Exception as exc:
            return {"error": "Could not draft the message.", "detail": str(exc)}
        return {
            "status": "draft_ready",
            "subject": msg.get("subject"),
            "recipient": msg.get("recipient"),
        }


async def entrypoint(ctx: agents.JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model=config.GEMINI_LIVE_MODEL,
            voice=config.GEMINI_LIVE_VOICE,
            temperature=0.7,
        ),
        vad=silero.VAD.load(),
    )

    await session.start(room=ctx.room, agent=ClutchVoiceAgent())
    await session.generate_reply(
        instructions=(
            "Briefly greet the user as Clutch and ask what deadline crisis "
            "they're facing right now."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
