import datetime

from app.models.commitment import Status
from app.services.planner import build_plan, remaining_minutes

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def test_remaining_minutes_accounts_for_progress(make_commitment):
    c = make_commitment(est_effort_minutes=100, progress_pct=25)
    assert remaining_minutes(c) == 75.0


def test_on_track_when_plenty_of_time(make_commitment):
    c = make_commitment(
        deadline=NOW + datetime.timedelta(hours=10),
        est_effort_minutes=60,
        progress_pct=0,
    )
    plan = build_plan([c], NOW)
    assert plan["feasible"] is True
    assert plan["total_deficit_minutes"] == 0
    assert len(plan["schedule"]) == 1
    assert plan["schedule"][0]["risk"] == "on_track"


def test_deficit_when_not_enough_time(make_commitment):
    c = make_commitment(
        deadline=NOW + datetime.timedelta(minutes=30),
        est_effort_minutes=60,
        progress_pct=0,
    )
    plan = build_plan([c], NOW)
    assert plan["feasible"] is False
    assert plan["total_deficit_minutes"] == 30.0
    assert plan["schedule"][0]["risk"] == "deficit"
    assert plan["schedule"][0]["late_minutes"] == 30.0


def test_completed_work_leaves_nothing_to_schedule(make_commitment):
    c = make_commitment(est_effort_minutes=60, progress_pct=100)
    plan = build_plan([c], NOW)
    assert plan["schedule"] == []


def test_done_commitments_excluded(make_commitment):
    c = make_commitment(status=Status.done)
    plan = build_plan([c], NOW)
    assert plan["schedule"] == []


def test_cascade_orders_by_deadline(make_commitment):
    early = make_commitment(
        id=1, deadline=NOW + datetime.timedelta(hours=2), est_effort_minutes=60
    )
    late = make_commitment(
        id=2, deadline=NOW + datetime.timedelta(hours=8), est_effort_minutes=60
    )
    plan = build_plan([late, early], NOW)
    assert [row["id"] for row in plan["schedule"]] == [1, 2]
