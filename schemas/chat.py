from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    document_id: UUID
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    source_pages: list[int]
    chunks_used: int