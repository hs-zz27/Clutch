from typing import Any

from pydantic import BaseModel


class AgentRequest(BaseModel):
    goal: str = "I'm running out of time. Tell me what to do."


class AgentResponse(BaseModel):
    final_message: str
    trace: list[dict[str, Any]]
