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
