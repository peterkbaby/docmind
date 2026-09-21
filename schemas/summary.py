from uuid import UUID

from pydantic import BaseModel

class SummaryResponse(BaseModel):
    document_id: UUID
    summary: str
    source_pages: list[int]