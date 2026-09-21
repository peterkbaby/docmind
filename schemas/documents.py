from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from schemas.summary import SummaryResponse



class DocumentResponse(BaseModel):
    id: UUID
    owner_id: str
    filename: str
    title: str
    storage_key: str
    page_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    data: DocumentResponse
    summary: SummaryResponse | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int