from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings


_llm = ChatGoogleGenerativeAI(
    model=settings.llm_model,
    google_api_key=settings.llm_api_key,
)

SYSTEM_PROMPT = """You are a document assistant. Answer the user's question using ONLY the provided context.
Rules:
    -If the context doesn't contain enough information, say "I Don't have enough information to answer that."
    -Be concise and clear
    -Cite page numbers in your answer like [page 3].
    -If you don't know the answer, say "I Don't know.", don't make up an answer."""

SUMMARY_PROMPT = """Summarize the supplied document content using only the provided text.
 
Include:
- The document's main purpose
- Its most important points
- Important conclusions or recommendations
 
Rules:
- Write every point as a seperate bullet beginning with"- ".
- Do not invent missing information.
- Keep the summary concise and clearly structured.
- Cite relevant pages using [Page N]."""
 
 
def _response_text(content: str | list) -> str:
    if isinstance(content, str):
        return content
    
    return "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )

async def generate_answer(query: str, chunks: list[dict]) -> dict:
    context = "\n\n".join(
        f"[page {chunk['page_number']}]: {chunk['text']}" for chunk in chunks
    )

    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", f"Context:\n{context}\n\nQuestion: {query}")
    ]

    response = await _llm.ainvoke(messages)
    pages = sorted(set(c["page_number"] for c in chunks))

    answer = _response_text(response.content)

    return {
        "answer": answer,
        "source_pages": pages,
        "chunks_used": len(chunks)
    }

async def generate_summary(chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[page {chunk['page_number']}]: {chunk['text']}" for chunk in chunks
    )
    
    response = await _llm.ainvoke([
        ("system", SUMMARY_PROMPT),
        ("human", f"Document Content:\n{context}")
    ])
    
    return _response_text(response.content)