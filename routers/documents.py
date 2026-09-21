




import logging
from urllib.parse import quote
from uuid import UUID
from fastapi import APIRouter, File, Request, Depends, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from core.limiter import limiter
from core.dependencies import get_current_user
from core.config import settings
from database.db import get_session
from database.documents import Document
from core.storage import delete_from_s3, download_from_s3, upload_to_s3
from services.ingestion_service import ingest_document
from services.exceptions import DocumentNotFound, DocumentNotReady, FileTooLarge, InvalidFileType, QuotaExceeded
from schemas.documents import DocumentListResponse, DocumentResponse, DocumentUploadResponse
from services.summary_service import get_summary
from rag.qdrant_store import delete_document_vectors

logger = logging.getLogger(__name__)
docs = APIRouter(prefix="/docmind", tags=["documents"])




@docs.post("/documents/upload", response_model=DocumentUploadResponse)
@limiter.limit("3/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),

) -> DocumentUploadResponse:
    if file.content_type != "application/pdf":
        raise InvalidFileType("Only PDF files are supported")
    
    result = await session.execute(select(func.count(Document.id)).where(Document.owner_id == user_id))
    count = result.scalar_one()
    if count >= settings.max_documents_per_user:
        raise QuotaExceeded("You have reached the maximum number of documents")
    
    contents = await file.read()

    if len(contents) > settings.max_pdf_size_mb * 1024 * 1024:
        raise FileTooLarge("PDF file is too large")
    
    doc = Document(
        owner_id=user_id,
        filename=file.filename,
        title=file.filename,
        storage_key="",
        status="processing"
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    document_id = doc.id
    key = f"pdfs/{user_id}/{document_id}.pdf"
    s3_uploaded = False

    try:
        await upload_to_s3(contents, user_id, str(document_id))
        s3_uploaded = True

        doc.storage_key = key
        await session.commit()

        await ingest_document(session, doc, contents)
        await session.refresh(doc)
    except Exception:
        await session.rollback()

        if s3_uploaded:
            try:
                await delete_from_s3(key)
            except Exception:
                logger.exception("Failed to remove S3 object after ingestion failure")

        try:
            delete_document_vectors(
                document_id=str(document_id),
                owner_id=user_id,
            )
        except Exception:
            logger.exception("Failed to remove vectors after ingestion failure")

        persisted_doc = await session.get(Document, document_id)

        if persisted_doc is not None:
            await session.delete(persisted_doc)
            await session.commit()

        raise

    summary = None
    try:
        summary = await get_summary(session, document_id=document_id, owner_id=user_id)
    except Exception:
        await session.rollback()
        logger.exception("Summary generation failed for document %s", document_id)

    await session.refresh(doc)
    return DocumentUploadResponse(data=doc, summary=summary)


@docs.get("/documents", response_model=DocumentListResponse)
@limiter.limit("100/minute")
async def get_documents(
    request: Request,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentListResponse:

    result = await session.execute(select(Document).where(Document.owner_id == user_id).order_by(Document.created_at.desc()))
    documents = list(result.scalars().all())
    return DocumentListResponse(documents=documents, total=len(documents))


@docs.get("/documents/{document_id}", response_model=DocumentResponse)
@limiter.limit("60/minute")
async def get_document(
    request: Request,
    document_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    result = await session.execute(select(Document).where(Document.id == document_id, Document.owner_id == user_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise DocumentNotFound("Document not found")
    return document


@docs.get("/documents/{document_id}/content")
@limiter.limit("30/minute")
async def get_document_content(
    request: Request,
    document_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    result = await session.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == user_id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise DocumentNotFound("Document not found")
    if not document.storage_key:
        raise DocumentNotReady("Document content is not available")

    content = await download_from_s3(document.storage_key)
    filename = quote(document.filename)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{filename}",
            "Cache-Control": "private, max-age=300",
        },
    )


@docs.delete("/documents/{document_id}")
@limiter.limit("20/minute")
async def delete_document(
    request: Request,
    document_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    result = await session.execute(select(Document).where(Document.id == document_id, Document.owner_id == user_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise DocumentNotFound("Document not found")
    
    if document.storage_key:
        await delete_from_s3(document.storage_key)

    delete_document_vectors(
        document_id=str(document_id),
        owner_id=user_id,
    )

    await session.delete(document)
    await session.commit()

    return {"detail": "Document deleted"}
    
    