from uuid import UUID
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.summary_service import get_summary
from core.limiter import limiter
from database.db import get_session
from core.dependencies import get_current_user
from schemas.summary import SummaryResponse
from services.exceptions import DocumentNotFound, DocumentNotReady
from database.documents import Document

summaries = APIRouter(prefix="/summaries", tags=["summaries"])

@summaries.post("/documents/{document_id}/summary", response_model=SummaryResponse)
@limiter.limit("10/minute")
async def create_summary(
    request: Request,
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user),
) -> SummaryResponse:
    result = await get_summary(session, document_id, user_id)
    return SummaryResponse(**result)
    
@summaries.get("/documents/{document_id}/summary",response_model=SummaryResponse,)
@limiter.limit("10/minute")
async def get_summary_endpoint(
    request: Request,
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user),
) -> SummaryResponse:
    result = await session.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == user_id,
        )
    )
    document = result.scalar_one_or_none()
 
    if document is None:
        raise DocumentNotFound("Document not found")
 
    if document.summary is None:
        raise DocumentNotReady("Summary has not been generated")
 
    return SummaryResponse(
        document_id=document.id,
        summary=document.summary,
        source_pages=list(range(1, document.page_count + 1)),
    )