"""Schemas for the what-if simulation sandbox (feature #6).

A scenario is a set of hypothetical edits applied on top of the real
commitments. All fields are optional so the caller only sends what changes.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class EffortOverride(BaseModel):
    est_effort_minutes: int | None = Field(default=None, gt=0)
    effort_p80_minutes: int | None = Field(default=None, gt=0)


class HypotheticalCommitment(BaseModel):
    """A surprise task to inject into the scenario (never persisted)."""
    title: str
    deadline: datetime
    est_effort_minutes: int = Field(default=60, gt=0)
    effort_p80_minutes: int | None = Field(default=None, gt=0)
    importance: int = Field(default=3, ge=1, le=5)
    stakeholder: str | None = None
    depends_on_id: int | None = None


class WhatIfScenario(BaseModel):
    # commitments to pretend are dropped / already finished
    drop_ids: list[int] = Field(default_factory=list)
    complete_ids: list[int] = Field(default_factory=list)
    # id -> new deadline / new effort
    deadline_overrides: dict[int, datetime] = Field(default_factory=dict)
    effort_overrides: dict[int, EffortOverride] = Field(default_factory=dict)
    # e.g. pulling an all-nighter adds focus minutes on top of real capacity
    extra_focus_minutes: float = 0.0
    # surprise tasks that just landed
    add_commitments: list[HypotheticalCommitment] = Field(default_factory=list)
