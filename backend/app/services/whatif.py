"""Phase 9 feature #6 - what-if simulation sandbox.

Apply a hypothetical scenario to detached clones of the real commitments and
re-run the planner. Pure and side-effect free: we never touch the ORM session or
the database, so the user can stress-test ideas ('what if I drop the blog post
and pull an all-nighter?') without consequences.

The reported deficit is the PLAN's deadline-aware deficit (sequential lateness
on real working time), not a single capacity pool. That is what makes the
baseline meaningful: a task due at 10am can't be made up at 8pm, and only the
sequential plan sees that. 'Extra focus / skip sleep' is modeled as work done
right now - it shaves minutes off the soonest-due tasks so the planner has less
to fit into normal hours.
"""
from __future__ import annotations

import datetime
from types import SimpleNamespace

from app.models.commitment import Status
from app.services import capacity as capacity_service
from app.services import planner as planner_service
from app.services import triage as triage_service
from app.schemas.whatif import WhatIfScenario

# synthetic ids for injected hypothetical tasks (negative => never collide)
_HYPO_ID_START = -1

def _aware(dt: datetime.datetime | None) -> datetime.datetime | None:
    """Treat a naive scenario datetime as UTC so it never clashes with the
    tz-aware clock inside the planner/triage."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def _clone(c) -> SimpleNamespace:
    return SimpleNamespace(
        id=c.id,
        title=c.title,
        description=getattr(c, "description", None),
        deadline=c.deadline,
        est_effort_minutes=c.est_effort_minutes,
        effort_p80_minutes=c.effort_p80_minutes,
        importance=c.importance,
        stakeholder=c.stakeholder,
        min_viable_definition=c.min_viable_definition,
        depends_on_id=c.depends_on_id,
        status=c.status,
        progress_pct=c.progress_pct,
    )

def apply_scenario(commitments: list, scenario: WhatIfScenario) -> list:
    clones = [_clone(c) for c in commitments]
    drop = set(scenario.drop_ids)
    done = set(scenario.complete_ids)

    for c in clones:
        if c.id in drop:
            c.status = Status.dropped
        if c.id in done:
            c.progress_pct = 100
            c.status = Status.done
        if c.id in scenario.deadline_overrides:
            c.deadline = _aware(scenario.deadline_overrides[c.id])
        if c.id in scenario.effort_overrides:
            ov = scenario.effort_overrides[c.id]
            if ov.est_effort_minutes is not None:
                c.est_effort_minutes = ov.est_effort_minutes
            if ov.effort_p80_minutes is not None:
                c.effort_p80_minutes = ov.effort_p80_minutes

    next_id = _HYPO_ID_START
    for h in scenario.add_commitments:
        clones.append(
            SimpleNamespace(
                id=next_id,
                title=h.title,
                description=None,
                deadline=_aware(h.deadline),
                est_effort_minutes=h.est_effort_minutes,
                effort_p80_minutes=h.effort_p80_minutes,
                importance=h.importance,
                stakeholder=h.stakeholder,
                min_viable_definition=None,
                depends_on_id=h.depends_on_id,
                status=Status.not_started,
                progress_pct=0,
            )
        )
        next_id -= 1

    return clones

def _apply_extra_focus(clones: list, extra_minutes: float | None) -> None:
    """Model 'skip sleep / pull an all-nighter' as work already done now: shave
    `extra_minutes` off the soonest-due unfinished tasks (each floored at 1 min)
    so the planner sees less remaining effort to fit into normal working hours."""
    if not extra_minutes or extra_minutes <= 0:
        return
    remaining = float(extra_minutes)
    active = [c for c in clones if c.status not in (Status.done, Status.dropped)]
    active.sort(key=lambda c: c.deadline)
    for c in active:
        if remaining <= 0:
            break
        effort = float(c.est_effort_minutes or 0)
        if effort <= 1:
            continue
        shave = min(remaining, effort - 1)
        ratio = (effort - shave) / effort
        c.est_effort_minutes = max(1, int(round(effort - shave)))
        if c.effort_p80_minutes:
            c.effort_p80_minutes = max(1, int(round(c.effort_p80_minutes * ratio)))
        remaining -= shave

def simulate(
    commitments: list,
    now: datetime.datetime,
    scenario: WhatIfScenario,
    *,
    busy_blocks: list[tuple[datetime.datetime, datetime.datetime]] | None = None,
    policy: capacity_service.WorkPolicy | None = None,
    base_capacity_minutes: float | None = None,
    calibration_factor: float = 1.0,
) -> dict:
    blocks = busy_blocks or []

    base_plan = planner_service.build_plan(
        list(commitments), now, calibration_factor, busy_blocks=blocks, policy=policy
    )
    base_triage = triage_service.run_triage(
        list(commitments),
        now,
        capacity_minutes=base_capacity_minutes,
        calibration_factor=calibration_factor,
        busy_blocks=blocks,
        policy=policy,
    )

    scenario_commitments = apply_scenario(commitments, scenario)
    _apply_extra_focus(scenario_commitments, scenario.extra_focus_minutes)

    scenario_capacity = base_capacity_minutes
    if base_capacity_minutes is not None and scenario.extra_focus_minutes:
        scenario_capacity = max(
            base_capacity_minutes + scenario.extra_focus_minutes, 0.0
        )

    scen_plan = planner_service.build_plan(
        scenario_commitments, now, calibration_factor, busy_blocks=blocks, policy=policy
    )
    scen_triage = triage_service.run_triage(
        scenario_commitments,
        now,
        capacity_minutes=scenario_capacity,
        calibration_factor=calibration_factor,
        busy_blocks=blocks,
        policy=policy,
    )

    diff = {
        "deficit_minutes_before": base_plan["total_deficit_minutes"],
        "deficit_minutes_after": scen_plan["total_deficit_minutes"],
        "deficit_minutes_delta": scen_plan["total_deficit_minutes"]
        - base_plan["total_deficit_minutes"],
        "feasible_before": base_plan["feasible"],
        "feasible_after": scen_plan["feasible"],
        "make_probability_before": base_plan["make_probability"],
        "make_probability_after": scen_plan["make_probability"],
        "worst_case_deficit_before": base_plan["total_deficit_minutes_p80"],
        "worst_case_deficit_after": scen_plan["total_deficit_minutes_p80"],
    }

    return {
        "now": now,
        "calibration_factor": calibration_factor,
        "baseline": {"plan": base_plan, "triage": base_triage},
        "scenario": {"plan": scen_plan, "triage": scen_triage},
        "diff": diff,
    }
