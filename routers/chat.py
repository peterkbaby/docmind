from fastapi import APIRouter, Depends, Request

from schemas.chat import ChatRequest, ChatResponse
from core.dependencies import get_current_user
from core.limiter import limiter
from services.retrieval_service import retrieve_documents
from rag.chains import generate_answer
 
chat = APIRouter(prefix="/docmind", tags=["DocMind Chat"])


@chat.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    body: ChatRequest,
    user_id: str = Depends(get_current_user),
) -> ChatResponse:
    chunks = await retrieve_documents(body.question, str(body.document_id), user_id)

    if not chunks:
        return ChatResponse(
            answer="No relevant content found in this document",
            source_pages=[],
            chunks_used=0,
        )
    
    result = await generate_answer(body.question, chunks)
    return ChatResponse(**result)