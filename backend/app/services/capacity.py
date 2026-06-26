"""Phase 6.5 - realistic focus-capacity engine.

The naive planner assumed every minute between now and a deadline was usable.
That is wrong: people sleep, attend classes, and have meetings. This module
computes the *actually usable* focus minutes in a window by:

  1. counting only a daily work window (local to TIMEZONE),
  2. capping each day at MAX_FOCUS_HOURS_PER_DAY (you can't focus 14h straight),
  3. subtracting busy blocks (meetings/classes/sleep) that overlap the window.

It is a pure function of its inputs - no DB, no network - so it is fully
deterministic and easy to unit-test. All datetimes must be timezone-aware.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from app.core.config import settings

@dataclass(frozen=True)
class WorkPolicy:
    timezone: str
    day_start_hour: int
    day_end_hour: int
    max_focus_hours_per_day: float

def policy_from_settings() -> WorkPolicy:
    return WorkPolicy(
        timezone=settings.TIMEZONE,
        day_start_hour=settings.WORK_DAY_START_HOUR,
        day_end_hour=settings.WORK_DAY_END_HOUR,
        max_focus_hours_per_day=settings.MAX_FOCUS_HOURS_PER_DAY,
    )

def _overlap_minutes(
    a_start: datetime.datetime,
    a_end: datetime.datetime,
    b_start: datetime.datetime,
    b_end: datetime.datetime,
) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    return max((end - start).total_seconds() / 60.0, 0.0)

def available_minutes(
    start: datetime.datetime,
    end: datetime.datetime,
    busy_blocks: list[tuple[datetime.datetime, datetime.datetime]],
    policy: WorkPolicy,
) -> float:
    """Usable focus minutes in [start, end). All datetimes must be tz-aware.

    busy_blocks is an iterable of (block_start, block_end) tz-aware pairs.
    Invalid policies (end hour <= start hour) yield 0 rather than raising.
    """
    if end <= start:
        return 0.0
    if not (0 <= policy.day_start_hour < policy.day_end_hour <= 23):
        return 0.0

    tz = ZoneInfo(policy.timezone)
    start_local = start.astimezone(tz)
    end_local = end.astimezone(tz)
    max_focus = max(policy.max_focus_hours_per_day, 0.0) * 60.0

    total = 0.0
    day = start_local.date()
    last_day = end_local.date()
    while day <= last_day:
        win_start = datetime.datetime.combine(
            day, datetime.time(policy.day_start_hour), tzinfo=tz
        )
        win_end = datetime.datetime.combine(
            day, datetime.time(policy.day_end_hour), tzinfo=tz
        )
        usable_start = max(win_start, start_local)
        usable_end = min(win_end, end_local)
        window_min = max(
            (usable_end - usable_start).total_seconds() / 60.0, 0.0
        )
        if window_min > 0:
            busy_min = 0.0
            for block_start, block_end in busy_blocks:
                busy_min += _overlap_minutes(
                    usable_start,
                    usable_end,
                    block_start.astimezone(tz),
                    block_end.astimezone(tz),
                )
            day_available = max(window_min - busy_min, 0.0)
            total += min(day_available, max_focus)
        day += datetime.timedelta(days=1)

    return total

def _free_intervals(
    window_start: datetime.datetime,
    window_end: datetime.datetime,
    busy_blocks: list[tuple[datetime.datetime, datetime.datetime]],
    tz: ZoneInfo,
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """Sub-intervals of [window_start, window_end) that are NOT busy."""
    clipped: list[tuple[datetime.datetime, datetime.datetime]] = []
    for b_start, b_end in busy_blocks:
        s = max(window_start, b_start.astimezone(tz))
        e = min(window_end, b_end.astimezone(tz))
        if e > s:
            clipped.append((s, e))
    clipped.sort()
    free: list[tuple[datetime.datetime, datetime.datetime]] = []
    cursor = window_start
    for s, e in clipped:
        if s > cursor:
            free.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < window_end:
        free.append((cursor, window_end))
    return free

def advance_working_minutes(
    start: datetime.datetime,
    minutes: float,
    busy_blocks: list[tuple[datetime.datetime, datetime.datetime]],
    policy: WorkPolicy,
    max_days: int = 60,
) -> datetime.datetime:
    """Datetime at which `minutes` of focus work, begun at `start`, are finished.

    The inverse of available_minutes: instead of counting usable minutes in a
    window, it walks forward through daily work windows (skipping nights),
    subtracting busy blocks and honoring the per-day focus cap, until the
    requested minutes are consumed. This lets the planner project finishes on
    *real* time, so it agrees with the capacity meter instead of pretending the
    user works straight through the night.

    Notes:
      - The per-day cap is applied per call (per task) - an accepted
        simplification. Work-hours and busy blocks (the dominant effects) are
        exact.
      - Returns `start` unchanged for minutes <= 0 and falls back to raw
        wall-clock if the policy is invalid, so it never raises.
    """
    if minutes <= 0:
        return start
    if not (0 <= policy.day_start_hour < policy.day_end_hour <= 23):
        return start + datetime.timedelta(minutes=minutes)

    tz = ZoneInfo(policy.timezone)
    start_local = start.astimezone(tz)
    max_focus = max(policy.max_focus_hours_per_day, 0.0) * 60.0
    if max_focus <= 0:
        return start + datetime.timedelta(minutes=minutes)

    remaining = float(minutes)
    day = start_local.date()
    last_day = day + datetime.timedelta(days=max_days)
    while day <= last_day:
        win_start = datetime.datetime.combine(
            day, datetime.time(policy.day_start_hour), tzinfo=tz
        )
        win_end = datetime.datetime.combine(
            day, datetime.time(policy.day_end_hour), tzinfo=tz
        )
        usable_start = max(win_start, start_local)
        if usable_start < win_end:
            day_used = 0.0
            for f_start, f_end in _free_intervals(
                usable_start, win_end, busy_blocks, tz
            ):
                cap_left = max_focus - day_used
                if cap_left <= 0:
                    break
                seg = (f_end - f_start).total_seconds() / 60.0
                usable = min(seg, cap_left)
                if remaining <= usable:
                    return f_start + datetime.timedelta(minutes=remaining)
                remaining -= usable
                day_used += usable
        day += datetime.timedelta(days=1)

    # Could not place the work within the guard window: flag it as clearly late.
    return datetime.datetime.combine(
        last_day, datetime.time(policy.day_end_hour), tzinfo=tz
    )
