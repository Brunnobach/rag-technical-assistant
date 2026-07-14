"""Document ingestion pipeline.

Extracts text from PDFs, splits it into overlapping chunks, and persists them
into the vector store with source metadata.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pypdf import PdfReader

if TYPE_CHECKING:
    from rag_technical_assistant.retrieval import VectorStore

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from a PDF file."""
    reader = PdfReader(str(file_path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            pages.append(f"\n\n--- Page {page_number} ---\n\n{text.strip()}")
    if not pages:
        raise ValueError(f"No text could be extracted from {file_path}")
    return "".join(pages)


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list[tuple[int, str]]:
    """Split text into overlapping chunks of approximately chunk_size words.

    Returns a list of tuples (chunk_index, chunk_text).
    """
    words = text.split()
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    step = max(1, chunk_size - chunk_overlap)
    i = 0
    while i < len(words):
        chunk = words[i : i + chunk_size]
        chunks.append(" ".join(chunk))
        i += step

    return list(enumerate(chunks))


def ingest_file(
    file_path: Path,
    vector_store: "VectorStore",
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[dict]:
    """Ingest a single PDF into the vector store.

    The document is chunked, embedded, and stored with metadata including the
    document name, chunk index, and page number when available.
    """
    file_path = Path(file_path)
    document_name = file_path.name
    logger.info("Ingesting %s", document_name)

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    records = []
    for chunk_index, chunk_text_item in chunks:
        # Derive page number from the chunk if it contains a page marker
        page = _extract_page(chunk_text_item)
        records.append(
            {
                "text": chunk_text_item,
                "metadata": {
                    "document": str(document_name),
                    "chunk_index": str(chunk_index),
                    "page": str(page) if page is not None else "",
                    "source_file": str(file_path),
                },
            }
        )

    vector_store.add_documents(records)
    logger.info("Indexed %d chunks from %s", len(records), document_name)
    return records


def _extract_page(text: str) -> int | None:
    """Try to parse the first page marker inside a chunk."""
    import re

    match = re.search(r"---\s*Page\s+(\d+)\s*---", text)
    if match:
        return int(match.group(1))
    return None
