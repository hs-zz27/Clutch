from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.busy_block import BusySource


class BusyBlockCreate(BaseModel):
    start: datetime
    end: datetime
    label: str | None = None

    @model_validator(mode="after")
    def _check_order(self) -> "BusyBlockCreate":
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class BusyBlockRead(BaseModel):
    id: int
    start: datetime
    end: datetime
    label: str | None = None
    source: BusySource
    external_uid: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CapacityRead(BaseModel):
    from_time: datetime
    until: datetime
    available_minutes: float
    available_hours: float
