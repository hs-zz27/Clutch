import datetime

from app.services.capacity import WorkPolicy, available_minutes

UTC = datetime.timezone.utc


def _dt(year, month, day, hour, minute=0):
    return datetime.datetime(year, month, day, hour, minute, tzinfo=UTC)


POLICY = WorkPolicy(
    timezone="UTC", day_start_hour=9, day_end_hour=17, max_focus_hours_per_day=24
)


def test_full_work_window_single_day():
    mins = available_minutes(_dt(2026, 1, 1, 9), _dt(2026, 1, 1, 17), [], POLICY)
    assert mins == 480.0


def test_clipped_to_work_window():
    # Asking for the whole day still only counts the 09:00-17:00 window.
    mins = available_minutes(_dt(2026, 1, 1, 0), _dt(2026, 1, 1, 23), [], POLICY)
    assert mins == 480.0


def test_daily_focus_cap_limits_window():
    capped = WorkPolicy(
        timezone="UTC", day_start_hour=9, day_end_hour=17, max_focus_hours_per_day=4
    )
    mins = available_minutes(_dt(2026, 1, 1, 9), _dt(2026, 1, 1, 17), [], capped)
    assert mins == 240.0


def test_busy_block_inside_window_is_subtracted():
    busy = [(_dt(2026, 1, 1, 10), _dt(2026, 1, 1, 11))]
    mins = available_minutes(_dt(2026, 1, 1, 9), _dt(2026, 1, 1, 17), busy, POLICY)
    assert mins == 420.0


def test_busy_block_outside_window_is_ignored():
    busy = [(_dt(2026, 1, 1, 3), _dt(2026, 1, 1, 5))]
    mins = available_minutes(_dt(2026, 1, 1, 9), _dt(2026, 1, 1, 17), busy, POLICY)
    assert mins == 480.0


def test_multi_day_sums_each_day():
    mins = available_minutes(_dt(2026, 1, 1, 9), _dt(2026, 1, 2, 17), [], POLICY)
    assert mins == 960.0


def test_zero_when_end_before_start():
    assert (
        available_minutes(_dt(2026, 1, 1, 17), _dt(2026, 1, 1, 9), [], POLICY) == 0.0
    )


def test_zero_when_policy_window_invalid():
    bad = WorkPolicy(
        timezone="UTC", day_start_hour=17, day_end_hour=9, max_focus_hours_per_day=8
    )
    assert (
        available_minutes(_dt(2026, 1, 1, 0), _dt(2026, 1, 2, 0), [], bad) == 0.0
    )
