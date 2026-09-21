from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.documents import Document, DocumentChunk
from rag.chains import generate_summary
from services.exceptions import DocumentNotFound, DocumentNotReady



async def get_summary(
    session: AsyncSession,
    document_id: UUID,
    owner_id: str,

) -> dict:
    result = await session.execute(select(Document).where(Document.id == document_id, Document.owner_id == owner_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise DocumentNotFound("Document not found")
    
    if document.status != 'ready':
        raise DocumentNotReady("Document is not ready for summarization")

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index))
    db_chunks = list(result.scalars().all())

    if not db_chunks:
        raise DocumentNotReady("Document has no processed content")

    chunks = [
        {
            "text": chunk.content,
            "page_number": chunk.page_number,
        }
        for chunk in db_chunks
    ]


    summary = await generate_summary(chunks)

    update_result = await session.execute(update(Document).where(
        Document.id == document_id, 
        Document.owner_id == owner_id,
    ).values(
        summary=summary,
        summary_generated_at=datetime.now(timezone.utc),
    ).execution_options(synchronize_session=False)
    )

    if update_result.rowcount == 0:
        await session.rollback()
        raise DocumentNotFound("Document was deleted while its summary was being generated")
    
    await session.commit()

    return {
        "document_id": document_id,
        "summary": summary,
        "source_pages": sorted({chunk.page_number for chunk in db_chunks}),
    }