"""Phase 2 - Reverse-clock critical-path planner.

Schedules pending commitments by deadline and reports, for each, when it would
finish and whether that is too late. Estimates are chronically optimistic, so
beyond the expected (p50) effort we also track a worst-case (p80) effort and
report the deficit as a range plus a rough probability the user makes it
(feature #3 - confidence-scored estimates + risk buffers).
"""
import datetime

from app.models.commitment import Commitment, Status

# multiplier applied to the expected estimate when no explicit worst case is set
DEFAULT_P80_MULTIPLIER = 1.5


def _effort_p80(commitment: Commitment) -> float:
    """Worst-case total effort. Falls back to a multiple of the expected value
    so we never plan on the bare optimistic number."""
    if commitment.effort_p80_minutes and commitment.effort_p80_minutes > 0:
        return float(commitment.effort_p80_minutes)
    return commitment.est_effort_minutes * DEFAULT_P80_MULTIPLIER


def remaining_minutes(commitment: Commitment) -> float:
    """Expected (p50) minutes of work left, scaled by progress made."""
    total_time = commitment.est_effort_minutes
    completed = total_time * commitment.progress_pct / 100.0
    return total_time - completed


def remaining_minutes_p80(commitment: Commitment) -> float:
    """Worst-case (p80) minutes of work left, scaled by progress made."""
    total = _effort_p80(commitment)
    completed = total * commitment.progress_pct / 100.0
    return total - completed


def _make_probability(expected_deficit: float, worst_deficit: float) -> str:
    """Coarse 'will I make it?' signal from the expected vs worst-case deficit."""
    if worst_deficit <= 0:
        return "high"      # on track even in the worst case
    if expected_deficit <= 0:
        return "medium"    # makes it on the expected case, at risk on the worst
    return "low"           # behind even on the optimistic estimate


def build_plan(commitments: list[Commitment], now: datetime.datetime) -> dict:
    filtered_commitments = [
        c for c in commitments
        if c.status in (Status.not_started, Status.in_progress)
    ]

    filtered_commitments.sort(key=lambda c: (c.deadline, -c.importance))

    clock = now
    clock_p80 = now
    schedule = []
    total_deficit_minutes = 0.0
    total_deficit_minutes_p80 = 0.0

    for c in filtered_commitments:
        rem_mins = remaining_minutes(c)
        if rem_mins <= 0:
            continue
        rem_mins_p80 = remaining_minutes_p80(c)

        projected_finish = clock + datetime.timedelta(minutes=rem_mins)
        projected_finish_p80 = clock_p80 + datetime.timedelta(minutes=rem_mins_p80)
        latest_start = c.deadline - datetime.timedelta(minutes=rem_mins)

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
        "schedule": schedule,
        "total_deficit_minutes": total_deficit_minutes,
        "total_deficit_minutes_p80": total_deficit_minutes_p80,
        "feasible": total_deficit_minutes == 0,
        "feasible_worst_case": total_deficit_minutes_p80 == 0,
        "make_probability": _make_probability(
            total_deficit_minutes, total_deficit_minutes_p80
        ),
    }
