import datetime

from app.models.commitment import Status
from app.services.triage import pending_commitments, run_triage

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
FUTURE = NOW + datetime.timedelta(hours=10)


def _decision_for(result, cid):
    return next(d for d in result["decisions"] if d["id"] == cid)


def test_pending_excludes_done_and_completed(make_commitment):
    a = make_commitment(id=1, status=Status.not_started, progress_pct=0)
    b = make_commitment(id=2, status=Status.done)
    c = make_commitment(id=3, status=Status.in_progress, progress_pct=100)
    assert [x.id for x in pending_commitments([a, b, c])] == [1]


def test_no_deficit_marks_everything_do_fully(make_commitment):
    c = make_commitment(id=1, deadline=FUTURE, est_effort_minutes=60)
    result = run_triage([c], NOW, capacity_minutes=120)
    assert result["feasible"] is True
    assert result["deficit_minutes"] == 0
    assert result["capacity_minutes"] == 120
    assert _decision_for(result, 1)["decision"] == "DO_FULLY"


def test_capacity_override_is_respected(make_commitment):
    c = make_commitment(id=1, deadline=FUTURE, est_effort_minutes=60)
    result = run_triage([c], NOW, capacity_minutes=10)
    assert result["capacity_minutes"] == 10
    assert result["required_minutes"] == 60
    assert result["deficit_minutes"] == 50
    assert result["feasible"] is False


def test_wall_clock_capacity_when_no_override(make_commitment):
    # 10h until deadline (600 min) vs 60 min required -> no deficit
    c = make_commitment(id=1, deadline=FUTURE, est_effort_minutes=60)
    result = run_triage([c], NOW)
    assert result["capacity_minutes"] == 600.0
    assert result["deficit_minutes"] == 0


def test_drop_when_no_stakeholder(make_commitment):
    c = make_commitment(
        id=1,
        deadline=FUTURE,
        est_effort_minutes=600,
        importance=1,
        stakeholder=None,
        min_viable_definition=None,
    )
    result = run_triage([c], NOW, capacity_minutes=0)
    assert _decision_for(result, 1)["decision"] == "DROP"


def test_defer_when_stakeholder_present(make_commitment):
    c = make_commitment(
        id=1,
        deadline=FUTURE,
        est_effort_minutes=600,
        importance=2,
        stakeholder="Prof. X",
        min_viable_definition=None,
    )
    result = run_triage([c], NOW, capacity_minutes=0)
    assert _decision_for(result, 1)["decision"] == "DEFER"


def test_do_minimally_for_important_task_with_mvd(make_commitment):
    c = make_commitment(
        id=1,
        deadline=FUTURE,
        est_effort_minutes=600,
        importance=5,
        stakeholder="Prof. X",
        min_viable_definition="Submit core results only",
    )
    result = run_triage([c], NOW, capacity_minutes=300)
    decision = _decision_for(result, 1)
    assert decision["decision"] == "DO_MINIMALLY"
    assert decision["salvage_minutes"] == 240.0
