import asyncio
from services.pdf_service import extract_chunks_from_pdf

async def main():
    # Replace with path to any PDF you have
    with open("Production_Readiness_Report.pdf", "rb") as f:
        pdf_bytes = f.read()

    chunks, page_count = await extract_chunks_from_pdf(pdf_bytes)

    print(f"Total pages: {page_count}")
    print(f"Total chunks: {len(chunks)}")

    for i, c in enumerate(chunks[:5]):
        print(f"\n--- chunk {i}, page {c['page_number']} ---")
        print(c["content"][:200])

asyncio.run(main())