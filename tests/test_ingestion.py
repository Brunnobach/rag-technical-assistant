"""Unit tests for the ingestion helpers."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rag_technical_assistant.ingestion import chunk_text, _extract_page


def test_chunk_text():
    text = " ".join([str(i) for i in range(100)])
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
    assert len(chunks) > 1
    for idx, chunk in chunks:
        assert isinstance(idx, int)
        assert isinstance(chunk, str)
        assert len(chunk.split()) <= 20


def test_extract_page():
    assert _extract_page("\n\n--- Page 12 ---\n\nsome text") == 12
    assert _extract_page("no page marker") is None
