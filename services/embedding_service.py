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

async def embed_chunks(
    chunks: Sequence[DocumentChunk],
    document_id: uuid.UUID,
    owner_id: str,
) -> None:
    """Embedded chunk texts and upsert vectors into qrant"""
    client=get_qdrant_client()
    points: list[PointStruct] =[]
    for chunk in chunks:
        vector = await _embeddings.aembed_query(chunk.content)
        points.append(
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
        )
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
    )