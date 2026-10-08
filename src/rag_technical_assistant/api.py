"""RAG Technical Assistant – FastAPI application.

Provides endpoints to upload PDFs, index them into a ChromaDB vector store,
query the indexed knowledge base with citations, and check service health.
The implementation uses only open-source components; no OpenAI API key is required.
"""

from __future__ import annotations

import logging
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_technical_assistant.generation import AnswerGenerator
from rag_technical_assistant.ingestion import ingest_file
from rag_technical_assistant.retrieval import VectorStore

logger = logging.getLogger("rag_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class Settings:
    """Runtime configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.data_dir = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
        self.docs_dir = Path(os.environ.get("DOCS_DIR", self.data_dir / "documents"))
        self.chroma_dir = Path(os.environ.get("CHROMA_DIR", self.data_dir / "chroma"))
        self.chroma_host = os.environ.get("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.environ.get("CHROMA_PORT", "8001"))
        self.collection_name = os.environ.get("COLLECTION_NAME", "technical_documents")
        self.embedding_model = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.chunk_size = int(os.environ.get("CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", "100"))
        self.top_k = int(os.environ.get("TOP_K", "4"))
        self.use_local_llm = os.environ.get("USE_LOCAL_LLM", "false").lower() == "true"


settings = Settings()


class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    question: str = Field(..., min_length=3, description="The question to answer from the indexed documents.")
    top_k: int | None = Field(None, ge=1, le=20, description="Number of chunks to retrieve; overrides the default.")


class Source(BaseModel):
    """A single cited source used to generate an answer."""

    document: str = Field(..., description="Name of the source document.")
    chunk_index: int = Field(..., description="Chunk index within the document.")
    page: int | None = Field(None, description="Page number, if available.")
    text: str = Field(..., description="Retrieved chunk text.")
    score: float = Field(..., description="Similarity score.")


class QueryResponse(BaseModel):
    """Response body for the /query endpoint."""

    answer: str
    sources: list[Source]


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    indexed_documents: int
    chunk_count: int


vector_store: VectorStore | None = None
answer_generator: AnswerGenerator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the vector store and generator on startup."""
    global vector_store, answer_generator

    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    vector_store = VectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.collection_name,
        embedding_model=settings.embedding_model,
    )
    answer_generator = AnswerGenerator(use_local_llm=settings.use_local_llm)

    logger.info("RAG Technical Assistant API started")
    yield

    logger.info("RAG Technical Assistant API shutting down")


app = FastAPI(
    title="RAG Technical Assistant",
    description="Retrieval-augmented assistant for technical documents.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return the health status and collection statistics."""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    stats = vector_store.get_stats()
    return HealthResponse(
        status="healthy",
        indexed_documents=stats.get("indexed_documents", 0),
        chunk_count=stats.get("chunk_count", 0),
    )


@app.post("/upload", response_model=dict[str, Any])
async def upload_pdf(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a PDF, chunk it, embed it and store the chunks in ChromaDB.

    The original file is saved under the configured documents directory so it can be
    referenced by citation later.
    """
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    dest_path = settings.docs_dir / safe_name

    try:
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
    except Exception as exc:
        logger.exception("Failed to save uploaded PDF")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}") from exc
    finally:
        await file.close()

    try:
        chunks = ingest_file(
            file_path=dest_path,
            vector_store=vector_store,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    except Exception as exc:
        logger.exception("Failed to ingest PDF")
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF: {exc}") from exc

    return {"filename": safe_name, "document": safe_name, "chunks_indexed": len(chunks)}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Answer a question using the indexed documents and return cited sources."""
    if vector_store is None or answer_generator is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        top_k = request.top_k if request.top_k is not None else settings.top_k
        results = vector_store.query(question=request.question, top_k=top_k)
    except Exception as exc:
        logger.exception("Vector search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    if not results:
        return QueryResponse(
            answer="I could not find any relevant information in the indexed documents.",
            sources=[],
        )

    try:
        answer, sources = answer_generator.generate(request.question, results)
    except Exception as exc:
        logger.exception("Answer generation failed")
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {exc}") from exc

    return QueryResponse(answer=answer, sources=sources)


@app.post("/reset")
async def reset() -> dict[str, str]:
    """Clear the ChromaDB collection and remove uploaded documents."""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    vector_store.reset()
    shutil.rmtree(settings.docs_dir, ignore_errors=True)
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "reset"}
