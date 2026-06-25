import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class Status(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    done = "done"
    dropped = "dropped"
    deferred = "deferred"


class Commitment(Base):
    __tablename__ = "commitments"
    
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    est_effort_minutes: Mapped[int] = mapped_column(Integer, default=60)
    importance: Mapped[int] = mapped_column(Integer, default=3)              #5 most, 1 least
    stakeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    min_viable_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.not_started)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    