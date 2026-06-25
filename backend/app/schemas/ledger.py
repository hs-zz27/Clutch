from datetime import datetime
from pydantic import BaseModel


class LedgerEntryRead(BaseModel):
    id: int
    action: str
    target_type: str
    target_id: int | None
    summary: str
    reasoning: str | None
    payload: dict
    reversible: bool
    undone: bool
    created_at: datetime

    model_config = {"from_attributes": True}
