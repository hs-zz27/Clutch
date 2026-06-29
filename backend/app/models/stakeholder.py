from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Stakeholder(Base):
    """A person commitments are owed to. Captures just enough relationship
    context to tailor the register of renegotiation messages.
    """

    __tablename__ = "stakeholders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    # free-form role, e.g. 'professor', 'manager', 'client', 'teammate', 'friend'
    relationship: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 1 = very casual ... 5 = very formal
    formality: Mapped[int] = mapped_column(Integer, default=3)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
