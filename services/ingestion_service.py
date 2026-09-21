from sqlalchemy.ext.asyncio import AsyncSession

from services.pdf_service import extract_chunks_from_pdf
from database.documents import Document, DocumentChunk
from services.exceptions import IngestionFailed
from services.embedding_service import embed_chunks


async def ingest_document(session: AsyncSession, document: Document, pdf_bytes: bytes) -> None:
    try:
        chunks, page_count = await extract_chunks_from_pdf(pdf_bytes)
        document.page_count = page_count

        if not chunks:
            raise IngestionFailed(
                "The PDF contains no extractable text. Scanned or image-only PDFs require OCR before upload."
            )

        db_chunks = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                content=chunk["content"],
            )
            for chunk in chunks
        ]
        session.add_all(db_chunks)
        await session.commit()
        
        for db_chunk in db_chunks:
            await session.refresh(db_chunk)

        await embed_chunks(db_chunks, document.id, document.owner_id)

        document.status = "ready"
        await session.commit()
    
    except Exception as e:
        await session.rollback()
        document.status = "failed"
        session.add(document)

        await session.commit()
        if isinstance(e, IngestionFailed):
            raise
        raise IngestionFailed(f"Failed to ingest document: {e}") from e