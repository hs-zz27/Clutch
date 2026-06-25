"""Shared test setup.

The app constructs a DB engine and a Gemini client at import time from settings.
We seed harmless placeholder env vars BEFORE importing any app module so those
constructors succeed offline - the unit tests here never actually open a socket.
"""
import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/clutch_test"
)
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import datetime  # noqa: E402

import pytest  # noqa: E402

from app.models.commitment import Commitment, Status  # noqa: E402

UTC = datetime.timezone.utc


@pytest.fixture
def make_commitment():
    """Factory for in-memory Commitment instances (no DB session needed)."""

    def _make(**overrides) -> Commitment:
        defaults = dict(
            id=1,
            title="Task",
            description=None,
            deadline=datetime.datetime(2026, 1, 1, 22, 0, tzinfo=UTC),
            est_effort_minutes=60,
            importance=3,
            stakeholder=None,
            min_viable_definition=None,
            status=Status.not_started,
            progress_pct=0,
        )
        defaults.update(overrides)
        return Commitment(**defaults)

    return _make
