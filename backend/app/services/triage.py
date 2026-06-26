"""Phase 4 - Triage / Salvage Engine.

When the reverse-clock planner reports a deficit (required effort > available
time), this module decides what to sacrifice. It frames the problem as a
value-vs-time tradeoff and buckets every pending commitment into one of:

    DO_FULLY      - protect it, finish it completely
    DO_MINIMALLY  - ship the minimum-viable version to save time
    DEFER         - push past the deadline via renegotiation (needs a stakeholder)
    DROP          - lowest value-per-minute, explicitly cut

The output is deterministic and explainable: every decision carries a reason.
The agent layer (Phase 3) turns these decisions into a human narrative.

Capacity: by default capacity is the raw wall-clock minutes until the last
deadline. Callers that know the user's *real* focus capacity (Phase 6.5 - work
policy minus busy blocks) can pass capacity_minutes to override it. Keeping it
optional means the engine never breaks when no calendar data is available.

Calibration: callers can pass the learned calibration_factor (Phase 9 feature
#4) so required/remaining minutes match GET /plan. Defaults to 1.0 (identity),
so behaviour is unchanged when there is no history.

The embedded plan is built on the SAME real working-time basis as GET /plan
when busy_blocks + policy are supplied, so the triage 'plan' never contradicts
the War Room timeline. Without them it falls back to raw wall-clock.
"""
from __future__ import annotations

import datetime

from app.models.commitment import Commitment, Status
from app.services import capacity as capacity_service
from app.services.planner import build_plan, remaining_minutes

# fraction of full effort a "minimum viable" version is assumed to take
MVD_EFFORT_FRACTION = 0.4

def _value_density(c: Commitment, calibration_factor: float = 1.0) -> float:
    """Importance earned per remaining minute. Higher = protect first."""
    rem = remaining_minutes(c, calibration_factor) or 1.0
    return c.importance / rem

def pending_commitments(commitments: list[Commitment]) -> list[Commitment]:
    """Commitments still needing work (shared by triage and capacity callers)."""
    return [
        c
        for c in commitments
        if c.status in (Status.not_started, Status.in_progress)
        and remaining_minutes(c) > 0
    ]

def run_triage(
    commitments: list[Commitment],
    now: datetime.datetime,
    capacity_minutes: float | None = None,
    calibration_factor: float = 1.0,
    *,
    busy_blocks: list[tuple[datetime.datetime, datetime.datetime]] | None = None,
    policy: capacity_service.WorkPolicy | None = None,
) -> dict:
    # Build the embedded plan on real focus time when a policy is supplied, so
    # it agrees with GET /plan instead of assuming work straight through the
    # night. Degrades to raw wall-clock when no calendar data is available.
    plan = build_plan(
        commitments,
        now,
        calibration_factor,
        busy_blocks=busy_blocks,
        policy=policy,
    )

    pending = pending_commitments(commitments)

    # capacity: prefer a caller-supplied real focus budget; otherwise fall back
    # to raw wall-clock minutes until the last deadline.
    if capacity_minutes is not None:
        capacity = max(capacity_minutes, 0.0)
    elif pending:
        horizon = max(c.deadline for c in pending)
        capacity = max((horizon - now).total_seconds() / 60.0, 0.0)
    else:
        capacity = 0.0

    required = sum(remaining_minutes(c, calibration_factor) for c in pending)
    deficit = max(required - capacity, 0.0)

    decisions: list[dict] = []

    if deficit <= 0:
        for c in pending:
            decisions.append(
                _decision(
                    c,
                    "DO_FULLY",
                    "Fits within the available time - no sacrifice needed.",
                    calibration_factor=calibration_factor,
                )
            )
        return _result(plan, capacity, required, 0.0, decisions)

    # deficit: protect the highest value-per-minute first
    ranked = sorted(
        pending,
        key=lambda c: _value_density(c, calibration_factor),
        reverse=True,
    )
    budget = capacity
    for c in ranked:
        rem = remaining_minutes(c, calibration_factor)
        if rem <= budget:
            decisions.append(
                _decision(
                    c,
                    "DO_FULLY",
                    f"High value for the time it costs ({c.importance}/5 in {rem:.0f} min); protected.",
                    calibration_factor=calibration_factor,
                )
            )
            budget -= rem
            continue

        mvd_effort = rem * MVD_EFFORT_FRACTION
        if c.importance >= 4 and c.min_viable_definition and mvd_effort <= budget:
            decisions.append(
                _decision(
                    c,
                    "DO_MINIMALLY",
                    (
                        f"Too big to finish fully, but important ({c.importance}/5). "
                        f"Ship the minimum-viable version (~{mvd_effort:.0f} min) instead."
                    ),
                    salvage_minutes=mvd_effort,
                    calibration_factor=calibration_factor,
                )
            )
            budget -= mvd_effort
        elif c.stakeholder:
            decisions.append(
                _decision(
                    c,
                    "DEFER",
                    (
                        f"No time left, but '{c.stakeholder}' can likely be renegotiated - "
                        f"push the deadline rather than drop it."
                    ),
                    calibration_factor=calibration_factor,
                )
            )
        else:
            decisions.append(
                _decision(
                    c,
                    "DROP",
                    f"Lowest value for its time cost and no one to renegotiate with - cut it to save {rem:.0f} min.",
                    calibration_factor=calibration_factor,
                )
            )

    return _result(plan, capacity, required, deficit, decisions)

def _decision(
    c: Commitment,
    decision: str,
    reason: str,
    salvage_minutes: float | None = None,
    calibration_factor: float = 1.0,
) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "importance": c.importance,
        "remaining_minutes": remaining_minutes(c, calibration_factor),
        "stakeholder": c.stakeholder,
        "decision": decision,
        "reason": reason,
        "salvage_minutes": salvage_minutes,
    }

def _result(plan: dict, capacity: float, required: float, deficit: float, decisions: list[dict]) -> dict:
    return {
        "feasible": deficit <= 0,
        "capacity_minutes": capacity,
        "required_minutes": required,
        "deficit_minutes": deficit,
        "decisions": decisions,
        "plan": plan,
    }
