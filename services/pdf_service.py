import os
import tempfile
from typing import BinaryIO
import unicodedata


from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings

def clean_extracted_text(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\x00", ""))

async def extract_chunks_from_pdf(
    pdf_bytes: bytes,
    chunk_size:int |None = None,
    chunk_overlap: int | None =None,
) -> tuple[list[dict], int]:
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name
        ocr_path = None
 
    try:
        pages = PyPDFLoader(tmp_path).load()

        if not any(page.page_content.strip() for page in pages):
            import ocrmypdf

            ocr_path = tmp_path + ".ocr.pdf"
            ocrmypdf.ocr(
                tmp_path,
                ocr_path,
                deskew=True,
                skip_text=True,
            )
            pages = PyPDFLoader(ocr_path).load()
    finally:
        os.unlink(tmp_path)

        if ocr_path and os.path.exists(ocr_path):
            os.unlink(ocr_path)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks: list[dict] =[]
    chunk_index=0

    for page_doc in pages:
        page_number = int(page_doc.metadata.get("page", 0)) + 1
        page_content = clean_extracted_text(page_doc.page_content)

        if not page_content.strip():
            continue

        page_chunks = text_splitter.split_text(page_content)

        for text in page_chunks:
            content = clean_extracted_text(text).strip()

            if not content:
                continue

            chunks.append(
                {
                    "content": content,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                }
            )
            chunk_index += 1
        
    return chunks, len(pages)
