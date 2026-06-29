import enum
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class BusySource(str, enum.Enum):
    manual = "manual"
    ics = "ics"


class BusyBlock(Base):
    """A span of unavailable time, subtracted from computed focus capacity.

    Sourced either manually (user-entered) or from an imported .ics feed. The
    pair (start, end) is stored timezone-aware so capacity math is unambiguous.
    """

    __tablename__ = "busy_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    label: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[BusySource] = mapped_column(
        Enum(BusySource, name="busy_source"),
        default=BusySource.manual,
        index=True,
    )
    # de-dup key for imported events (the ICS VEVENT UID); null for manual blocks
    external_uid: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
