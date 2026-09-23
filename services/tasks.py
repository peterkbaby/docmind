import asyncio
from core.celery_app import celery_app
from database.db import SessionLocal
from database.documents import Document
from services.ingestion_service import ingest_document
from core.storage import download_from_s3


@celery_app.task
def process_document(document_id: str):
    asyncio.run(_run(document_id))



async def _run(document_id: str):
    async with SessionLocal() as session:
        doc = await session.get(Document, document_id)
        if doc is None:
            return
        pdf_bytes = await download_from_s3(doc.storage_key)
        await ingest_document(session, doc, pdf_bytes)