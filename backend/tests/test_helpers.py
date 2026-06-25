import datetime

from app.services.agent_tools import _jsonable
from app.services.ics import _as_aware
from app.services.renegotiation import _split_subject_body
from app.services import mailer

UTC = datetime.timezone.utc


def test_split_subject_body_with_explicit_subject():
    text = "Subject: Extension request\n\nHi Prof, could I have two more days?"
    out = _split_subject_body(text, fallback_subject="Re: Task")
    assert out["subject"] == "Extension request"
    assert out["body"] == "Hi Prof, could I have two more days?"


def test_split_subject_body_falls_back_without_subject():
    text = "Hi Prof, could I have two more days?"
    out = _split_subject_body(text, fallback_subject="Re: Task")
    assert out["subject"] == "Re: Task"
    assert out["body"] == text


def test_mailer_is_configured_requires_both_credentials(monkeypatch):
    monkeypatch.setattr(mailer.settings, "GMAIL_SENDER", "")
    monkeypatch.setattr(mailer.settings, "GMAIL_APP_PASSWORD", "")
    assert mailer.is_configured() is False

    monkeypatch.setattr(mailer.settings, "GMAIL_SENDER", "me@example.com")
    monkeypatch.setattr(mailer.settings, "GMAIL_APP_PASSWORD", "")
    assert mailer.is_configured() is False

    monkeypatch.setattr(mailer.settings, "GMAIL_APP_PASSWORD", "app-password")
    assert mailer.is_configured() is True


def test_send_email_raises_when_not_configured(monkeypatch):
    monkeypatch.setattr(mailer.settings, "GMAIL_SENDER", "")
    monkeypatch.setattr(mailer.settings, "GMAIL_APP_PASSWORD", "")
    try:
        mailer.send_email("x@y.com", "subject", "body")
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError when mailer is unconfigured")


def test_jsonable_serializes_datetimes_recursively():
    dt = datetime.datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    out = _jsonable({"when": dt, "items": [dt, 1, "x"]})
    assert out["when"] == dt.isoformat()
    assert out["items"][0] == dt.isoformat()
    assert out["items"][1] == 1
    assert out["items"][2] == "x"


def test_as_aware_coerces_naive_and_skips_all_day_dates():
    naive = datetime.datetime(2026, 1, 1, 9, 0)
    aware = _as_aware(naive)
    assert aware is not None and aware.tzinfo is not None

    already_aware = datetime.datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    assert _as_aware(already_aware) == already_aware

    # all-day events arrive as a plain date and are not focus-time blocks
    assert _as_aware(datetime.date(2026, 1, 1)) is None
