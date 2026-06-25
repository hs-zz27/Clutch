from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent import run_agent
from app.services import ledger as ledger_service

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("", response_model=AgentResponse)
async def invoke_agent(payload: AgentRequest, db: AsyncSession = Depends(get_db)):
    """Run the Clutch agent against the user's current commitments."""
    result = await run_agent(db, payload.goal)
    final = (result.get("final_message") or "") if isinstance(result, dict) else ""
    trace = result.get("trace", []) if isinstance(result, dict) else []
    await ledger_service.record(
        db,
        action="agent_run",
        target_type="agent",
        summary=final[:200] or "Agent run",
        reasoning=payload.goal,
        payload={"goal": payload.goal, "steps": len(trace)},
        reversible=False,
    )
    return result
