from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str


class KnowledgeSearchResponse(BaseModel):
    answer: str
    citations: list[str]
