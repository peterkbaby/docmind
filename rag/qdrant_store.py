from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PayloadSchemaType,
    VectorParams,
)
from core.config import settings

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key
)

VECTOR_SIZE = 3072  

def init_qdrant_collection() -> None:
    """create collection at startup if it doesnt exist"""
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    client.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="document_id",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True,
    )
    client.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="owner_id",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True,
    )

def get_qdrant_client() -> QdrantClient:
    return client
    

def delete_document_vectors(
    document_id: str,
    owner_id: str,
) -> None:
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    ),
                    FieldCondition(
                        key="owner_id",
                        match=MatchValue(value=owner_id),
                    ),
                ]
            )
        ),
        wait=True,
    )
