from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent import run_agent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("", response_model=AgentResponse)
async def invoke_agent(payload: AgentRequest, db: AsyncSession = Depends(get_db)):
    """Run the Clutch agent against the user's current commitments."""
    return await run_agent(db, payload.goal)
