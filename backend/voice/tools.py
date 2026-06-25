"""Helpers that turn raw Clutch API payloads into compact, speakable summaries.

The voice model works best with terse, structured facts rather than full JSON
dumps. Each function returns a small dict the agent can reason over and read
aloud naturally.
"""
from __future__ import annotations

_INACTIVE = {"done", "dropped"}


def summarize_commitments(rows: list[dict]) -> dict:
    active = [r for r in rows if r.get("status") not in _INACTIVE]
    items = [
        {
            "id": r.get("id"),
            "title": r.get("title"),
            "deadline": r.get("deadline"),
            "importance": r.get("importance"),
            "status": r.get("status"),
            "progress_pct": r.get("progress_pct"),
        }
        for r in active
    ]
    return {"active_count": len(items), "commitments": items}


def summarize_plan(plan: dict) -> dict:
    schedule = plan.get("schedule", []) or []
    at_risk = [
        {
            "title": item.get("title"),
            "risk": item.get("risk"),
            "late_minutes": item.get("late_minutes"),
        }
        for item in schedule
        if item.get("risk") and item.get("risk") != "on_track"
    ]
    return {
        "feasible": plan.get("feasible"),
        "total_deficit_minutes": plan.get("total_deficit_minutes"),
        "at_risk": at_risk,
    }


def summarize_capacity(cap: dict) -> dict:
    return {
        "available_minutes": cap.get("available_minutes"),
        "available_hours": cap.get("available_hours"),
        "until": cap.get("until"),
    }
