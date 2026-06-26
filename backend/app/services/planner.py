"""Phase 2 - Reverse-clock critical-path planner.

Schedules pending commitments and reports, for each, when it would finish and
whether that is too late.

Three upgrades layer on top of the original earliest-deadline-first pass:
  - feature #3: estimates carry an expected (p50) and worst-case (p80) effort,
    so the deficit is reported as a range plus a rough 'make it' probability.
  - feature #1: commitments can depend on one another, so we schedule in true
    topological (critical-path) order and tighten each task's latest-start by
    its dependents' latest-starts.
  - feature #4: a learned calibration_factor scales every estimate toward how
    this person actually works (1.0 = no adjustment / not enough history yet).

Phase 6.5: when a work policy (+ busy blocks) is supplied, the forward pass
projects finishes on REAL focus time (skipping nights / meetings) via
capacity.advance_working_minutes, so the plan agrees with the capacity meter
instead of assuming the user works straight through the night. Without a
policy it falls back to the original raw wall-clock behaviour.

Everything degrades gracefully: no dependencies => earliest-deadline-first; no
worst-case estimate => 1.5x the expected value; no history => factor 1.0.
"""
import datetime

from app.models.commitment import Commitment
from app.services import capacity as capacity_service

# multiplier applied to the expected estimate when no explicit worst case is set
DEFAULT_P80_MULTIPLIER = 1.5

def _effort_p80(commitment: Commitment, calibration_factor: float = 1.0) -> float:
    """Worst-case total effort. Falls back to a multiple of the expected value
    so we never plan on the bare optimistic number, then scaled by the learned
    calibration factor."""
    if commitment.effort_p80_minutes and commitment.effort_p80_minutes > 0:
        base = float(commitment.effort_p80_minutes)
    else:
        base = commitment.est_effort_minutes * DEFAULT_P80_MULTIPLIER
    return base * calibration_factor

def remaining_minutes(
    commitment: Commitment, calibration_factor: float = 1.0
) -> float:
    """Expected (p50) minutes of work left, scaled by progress and calibration."""
    total_time = commitment.est_effort_minutes * calibration_factor
    completed = total_time * commitment.progress_pct / 100.0
    return total_time - completed

def remaining_minutes_p80(
    commitment: Commitment, calibration_factor: float = 1.0
) -> float:
    """Worst-case (p80) minutes of work left, scaled by progress and calibration."""
    total = _effort_p80(commitment, calibration_factor)
    completed = total * commitment.progress_pct / 100.0
    return total - completed

def _make_probability(expected_deficit: float, worst_deficit: float) -> str:
    """Coarse 'will I make it?' signal from the expected vs worst-case deficit."""
    if worst_deficit <= 0:
        return "high"      # on track even in the worst case
    if expected_deficit <= 0:
        return "medium"    # makes it on the expected case, at risk on the worst
    return "low"           # behind even on the optimistic estimate

def _topological_order(pending: list[Commitment]) -> list[int]:
    """Order ids so prerequisites come before dependents, tie-broken by
    (deadline, -importance). Dangling prerequisites (not pending) are ignored;
    cycles fall back to deadline order for whatever is left."""
    by_id = {c.id: c for c in pending}

    def prereq(c: Commitment) -> int | None:
        pid = c.depends_on_id
        return pid if pid in by_id and pid != c.id else None

    indeg = {c.id: (1 if prereq(c) is not None else 0) for c in pending}
    dependents: dict[int, list[int]] = {c.id: [] for c in pending}
    for c in pending:
        p = prereq(c)
        if p is not None:
            dependents[p].append(c.id)

    def sort_key(cid: int):
        c = by_id[cid]
        return (c.deadline, -c.importance)

    ready = [cid for cid, d in indeg.items() if d == 0]
    order: list[int] = []
    visited: set[int] = set()
    while ready:
        ready.sort(key=sort_key)
        cid = ready.pop(0)
        if cid in visited:
            continue
        visited.add(cid)
        order.append(cid)
        for dep in dependents[cid]:
            indeg[dep] -= 1
            if indeg[dep] == 0:
                ready.append(dep)

    if len(order) < len(pending):  # cycle: append leftovers by deadline
        leftover = [cid for cid in by_id if cid not in visited]
        leftover.sort(key=sort_key)
        order.extend(leftover)
    return order

def build_plan(
    commitments: list[Commitment],
    now: datetime.datetime,
    calibration_factor: float = 1.0,
    *,
    busy_blocks: list[tuple[datetime.datetime, datetime.datetime]] | None = None,
    policy: capacity_service.WorkPolicy | None = None,
) -> dict:
    blocks = busy_blocks or []

    def _advance(clock: datetime.datetime, minutes: float) -> datetime.datetime:
        """Project a finish: real working time when a policy is set, else raw."""
        if policy is not None:
            return capacity_service.advance_working_minutes(
                clock, minutes, blocks, policy
            )
        return clock + datetime.timedelta(minutes=minutes)

    from app.models.commitment import Status
    pending = [
        c
        for c in commitments
        if c.status in (Status.not_started, Status.in_progress)
        and remaining_minutes(c, calibration_factor) > 0
    ]
    by_id = {c.id: c for c in pending}
    order = _topological_order(pending)

    # dependents map (within pending) for the reverse latest-start pass
    dependents: dict[int, list[int]] = {cid: [] for cid in order}
    for c in pending:
        pid = c.depends_on_id
        if pid in by_id and pid != c.id:
            dependents[pid].append(c.id)

    # reverse pass: a task must finish before any dependent's latest start.
    eff_latest_start: dict[int, datetime.datetime] = {}
    for cid in reversed(order):
        c = by_id[cid]
        latest_finish = c.deadline
        for dep in dependents.get(cid, []):
            if dep in eff_latest_start:
                latest_finish = min(latest_finish, eff_latest_start[dep])
        eff_latest_start[cid] = latest_finish - datetime.timedelta(
            minutes=remaining_minutes(c, calibration_factor)
        )

    # forward pass: sequential schedule for expected (p50) and worst-case (p80)
    clock = now
    clock_p80 = now
    schedule = []
    total_deficit_minutes = 0.0
    total_deficit_minutes_p80 = 0.0

    for cid in order:
        c = by_id[cid]
        rem_mins = remaining_minutes(c, calibration_factor)
        rem_mins_p80 = remaining_minutes_p80(c, calibration_factor)

        projected_finish = _advance(clock, rem_mins)
        projected_finish_p80 = _advance(clock_p80, rem_mins_p80)
        latest_start = eff_latest_start.get(
            cid, c.deadline - datetime.timedelta(minutes=rem_mins)
        )

        late_minutes = 0.0
        if projected_finish > c.deadline:
            late_minutes = (projected_finish - c.deadline).total_seconds() / 60.0
        late_minutes_p80 = 0.0
        if projected_finish_p80 > c.deadline:
            late_minutes_p80 = (projected_finish_p80 - c.deadline).total_seconds() / 60.0

        if late_minutes > 0:
            risk = "deficit"
        elif latest_start <= now:
            risk = "at_risk"
        else:
            risk = "on_track"

        schedule.append({
            "id": c.id,
            "title": c.title,
            "importance": c.importance,
            "deadline": c.deadline,
            "depends_on_id": c.depends_on_id if c.depends_on_id in by_id else None,
            "remaining_minutes": rem_mins,
            "remaining_minutes_p80": rem_mins_p80,
            "projected_finish": projected_finish,
            "projected_finish_p80": projected_finish_p80,
            "latest_start": latest_start,
            "late_minutes": late_minutes,
            "late_minutes_p80": late_minutes_p80,
            "risk": risk,
        })

        total_deficit_minutes += late_minutes
        total_deficit_minutes_p80 += late_minutes_p80
        clock = projected_finish
        clock_p80 = projected_finish_p80

    return {
        "now": now,
        "calibration_factor": calibration_factor,
        "schedule": schedule,
        "total_deficit_minutes": total_deficit_minutes,
        "total_deficit_minutes_p80": total_deficit_minutes_p80,
        "feasible": total_deficit_minutes == 0,
        "feasible_worst_case": total_deficit_minutes_p80 == 0,
        "make_probability": _make_probability(
            total_deficit_minutes, total_deficit_minutes_p80
        ),
    }
