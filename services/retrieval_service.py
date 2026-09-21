from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue

from core.config import settings
from rag.qdrant_store import get_qdrant_client

_embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.llm_api_key
)

async def retrieve_documents(query: str, document_id: str, owner_id: str) -> list[dict]:
    query_vector = await _embeddings.aembed_query(query)
    client = get_qdrant_client()
    results = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                ),
                FieldCondition(
                    key="owner_id",
                    match=MatchValue(value=owner_id)
                )
            ]
        ),
        limit=settings.top_k,
        with_payload=True,
    )

    return [
        {
            "text": point.payload["text"],
            "page_number": point.payload["page_number"],
            "score": point.score
        }
        for point in results.points
    ]
    
