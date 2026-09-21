import asyncio
import uuid
from typing import Sequence

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client.models import PointStruct

from core.config import settings
from database.documents import DocumentChunk
from rag.qdrant_store import get_qdrant_client


_embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.llm_api_key,
)

EMBEDDING_BATCH_SIZE = 32


async def embed_chunks(
    chunks: Sequence[DocumentChunk],
    document_id: uuid.UUID,
    owner_id: str,
) -> None:
    """Embedded chunk texts and upsert vectors into qrant"""
    valid_chunks = [chunk for chunk in chunks if chunk.content.strip()]
    if not valid_chunks:
        raise ValueError("Cannot embed a document without text chunks")

    client = get_qdrant_client()
    for start in range(0, len(valid_chunks), EMBEDDING_BATCH_SIZE):
        batch = valid_chunks[start : start + EMBEDDING_BATCH_SIZE]
        vectors = await _embeddings.aembed_documents(
            [chunk.content for chunk in batch]
        )
        if len(vectors) != len(batch):
            raise ValueError("Embedding service returned an incomplete batch")

        points = [
            PointStruct(
                id=str(chunk.id),
                vector=vector,
                payload={
                    "document_id": str(document_id),
                    "owner_id": owner_id,
                    "chunk_id": str(chunk.id),
                    "page_number": chunk.page_number,
                    "text": chunk.content,
                },
            )
            for chunk, vector in zip(batch, vectors, strict=True)
        ]
        await asyncio.to_thread(
            client.upsert,
            collection_name=settings.qdrant_collection,
            points=points,
            wait=True,
        )
