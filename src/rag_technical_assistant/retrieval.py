"""Vector retrieval layer backed by ChromaDB.

Uses sentence-transformers for dense embeddings and a persistent ChromaDB
client for document storage and semantic search.
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """Thin wrapper around ChromaDB for our RAG use case."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8001,
        collection_name: str = "technical_documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._model = SentenceTransformer(embedding_model)

        # Prefer the remote ChromaDB service when host is not localhost for tests
        # In the default Docker setup the API talks to the chromadb service.
        if host in ("localhost", "127.0.0.1"):
            # Persistent local mode for testing without a running Chroma server
            self._client = chromadb.Client(
                ChromaSettings(anonymized_telemetry=False, is_persistent=False)
            )
        else:
            self._client = chromadb.HttpClient(host=host, port=port)

        self._collection = self._client.get_or_create_collection(name=collection_name)
        logger.info("Connected to ChromaDB collection '%s' on %s:%s", collection_name, host, port)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using the sentence-transformer model."""
        return self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False).tolist()

    def add_documents(self, records: list[dict[str, Any]]) -> None:
        """Add chunked documents to the vector store."""
        if not records:
            return

        ids = [f"{r['metadata']['document']}_{r['metadata']['chunk_index']}" for r in records]
        texts = [r["text"] for r in records]
        metadatas = [r["metadata"] for r in records]
        embeddings = self._embed(texts)

        self._collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    def query(self, question: str, top_k: int = 4) -> list[dict[str, Any]]:
        """Retrieve the top_k most relevant chunks for a question."""
        embedding = self._embed([question])[0]
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, max(1, self._collection.count())),
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0] or []
        metadatas = results.get("metadatas", [[]])[0] or []
        distances = results.get("distances", [[]])[0] or []

        out = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            # Convert cosine distance to a similarity score between 0 and 1
            score = max(0.0, 1.0 - distance)
            out.append(
                {
                    "text": text,
                    "metadata": metadata,
                    "score": round(score, 4),
                }
            )
        return out

    def get_stats(self) -> dict[str, int]:
        """Return statistics about the indexed collection."""
        count = self._collection.count()
        if count == 0:
            return {"indexed_documents": 0, "chunk_count": 0}

        all_meta = self._collection.get(include=["metadatas"])["metadatas"]
        documents = {m.get("document") for m in all_meta if m.get("document")}
        return {"indexed_documents": len(documents), "chunk_count": count}

    def reset(self) -> None:
        """Delete the current collection."""
        try:
            self._client.delete_collection(name=self.collection_name)
        except Exception:
            logger.warning("Could not delete collection %s; it may not exist", self.collection_name)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)
