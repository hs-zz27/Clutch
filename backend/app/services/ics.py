"""Optional ICS calendar-feed ingestion - import busy blocks without OAuth.

Many calendars (Google, Outlook, Apple) expose a private read-only .ics URL.
We fetch it, extract timed events as busy blocks, and swap them into the DB.

The `icalendar` dependency is OPTIONAL: the import is guarded so the core app
always runs. If the library or the feed URL is missing, sync raises a clear
error that the API turns into a 503/400 - nothing crashes.
"""
from __future__ import annotations

import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services import busy_blocks as busy_service

try:  # optional dependency
    import icalendar  # type: ignore
except ImportError:  # pragma: no cover - exercised only when extra not installed
    icalendar = None  # type: ignore

_FETCH_TIMEOUT = 15.0
_MAX_BYTES = 5 * 1024 * 1024  # never ingest an unbounded feed


class IcsNotAvailable(RuntimeError):
    """Raised when ICS sync cannot run (missing dep or unconfigured feed)."""


def is_available() -> bool:
    return icalendar is not None and bool(settings.CALENDAR_ICS_URL)


async def _fetch(url: str) -> str:
    async with httpx.AsyncClient(timeout=_FETCH_TIMEOUT, follow_redirects=True) as cx:
        resp = await cx.get(url)
        resp.raise_for_status()
        raw = resp.content[:_MAX_BYTES]
    return raw.decode("utf-8", errors="replace")


def _as_aware(value, tz: datetime.timezone = datetime.timezone.utc):
    """Coerce an ical date/datetime to a tz-aware datetime, or None to skip."""
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=tz)
        return value
    # all-day events arrive as a date; skip them - they are not focus-time blocks
    return None


def _parse(text: str) -> list[dict]:
    cal = icalendar.Calendar.from_ical(text)
    blocks: list[dict] = []
    for component in cal.walk("VEVENT"):
        dtstart = component.get("dtstart")
        dtend = component.get("dtend")
        if dtstart is None or dtend is None:
            continue
        start = _as_aware(dtstart.dt)
        end = _as_aware(dtend.dt)
        if start is None or end is None or end <= start:
            continue
        summary = component.get("summary")
        uid = component.get("uid")
        blocks.append(
            {
                "start": start,
                "end": end,
                "label": str(summary) if summary is not None else None,
                "external_uid": str(uid) if uid is not None else None,
            }
        )
    return blocks


async def sync(db: AsyncSession) -> dict:
    """Fetch the configured ICS feed and replace imported busy blocks.

    Raises IcsNotAvailable if the extra isn't installed or no URL is set.
    """
    if icalendar is None:
        raise IcsNotAvailable(
            "ICS support is not installed. Run: pip install -r requirements-optional.txt"
        )
    if not settings.CALENDAR_ICS_URL:
        raise IcsNotAvailable("No CALENDAR_ICS_URL is configured.")

    text = await _fetch(settings.CALENDAR_ICS_URL)
    blocks = _parse(text)
    count = await busy_service.replace_ics_blocks(db, blocks)
    return {"imported": count}
