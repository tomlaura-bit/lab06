from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    id: int
    filename: str
    sha256: str
    page_count: int
    blank_pages: int
    read_errors: int
    created_at: datetime
    chunk_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    document_id: int | None = None
    top_k: int | None = Field(default=None, ge=1, le=15)


class Passage(BaseModel):
    document: str
    page: int
    content: str
    score: float


class AskOut(BaseModel):
    answer: str
    passages: list[Passage]
    provider: str
