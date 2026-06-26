"""Schemas for automatic task decomposition (feature #5)."""
from pydantic import BaseModel, Field

class SubtaskSuggestion(BaseModel):
    title: str
    est_effort_minutes: int = Field(default=30, ge=1)   # expected (p50)
    effort_p80_minutes: int | None = Field(default=None, ge=1)  # worst case

class DecomposeBody(BaseModel):
    # when true, persist the suggested subtasks as a dependency-chained set
    persist: bool = False
