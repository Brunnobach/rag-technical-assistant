from fastapi.testclient import TestClient
import pytest
from fpdf import FPDF
import io
import os
import sys

# Ensure the src package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rag_technical_assistant.api import app, lifespan


@pytest.fixture(scope="module")
def client():
    """Create a TestClient that properly enters the FastAPI lifespan."""
    with TestClient(app) as test_client:
        yield test_client


def make_pdf(filename: str, text: str) -> bytes:
    """Create a simple in-memory PDF with the given text."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Encode text for fpdf; handle unicode by replacing unsupported characters
    safe_text = text.encode("latin-1", errors="replace").decode("latin-1")
    for line in safe_text.split("\n"):
        pdf.cell(0, 10, txt=line, ln=True)
    return pdf.output(dest="S")


@pytest.fixture(autouse=True)
def reset_store(client):
    """Reset the vector store before each test to keep tests isolated."""
    response = client.post("/reset")
    assert response.status_code == 200
    yield


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["indexed_documents"] == 0
    assert data["chunk_count"] == 0


def test_upload_pdf(client):
    text = "The quick brown fox jumps over the lazy dog. " * 50
    pdf_bytes = make_pdf("demo.pdf", text)
    response = client.post(
        "/upload",
        files={"file": ("demo.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "demo.pdf"
    assert data["chunks_indexed"] > 0

    health = client.get("/health").json()
    assert health["indexed_documents"] == 1
    assert health["chunk_count"] > 0


def test_query_with_citations(client):
    text = "The capital of Germany is Berlin. Berlin is the largest city in Germany." * 20
    pdf_bytes = make_pdf("germany.pdf", text)
    client.post(
        "/upload",
        files={"file": ("germany.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    response = client.post("/query", json={"question": "What is the capital of Germany?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert len(data["sources"]) > 0
    assert data["sources"][0]["document"] == "germany.pdf"


def test_query_no_results(client):
    response = client.post("/query", json={"question": "What is quantum computing?"})
    assert response.status_code == 200
    data = response.json()
    assert "I could not find" in data["answer"]
    assert data["sources"] == []


def test_upload_non_pdf_rejected(client):
    response = client.post(
        "/upload",
        files={"file": ("readme.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )
    assert response.status_code == 400


def test_reset_clears_data(client):
    text = "Some technical content." * 100
    pdf_bytes = make_pdf("reset.pdf", text)
    client.post(
        "/upload",
        files={"file": ("reset.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    health = client.get("/health").json()
    assert health["chunk_count"] > 0

    reset = client.post("/reset")
    assert reset.status_code == 200

    health = client.get("/health").json()
    assert health["chunk_count"] == 0
