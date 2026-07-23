# RAG Technical Assistant

A fully functional, production-oriented **Retrieval-Augmented Generation (RAG)** assistant for technical documents. Upload PDFs, ask questions, and receive answers grounded in your documents with cited sources.

Built for **Solutions Architect / Applied AI** portfolios targeting the DACH market.

---

## Live portfolio & desk UI

**Interactive desk:** https://brunnobach.github.io/rag-technical-assistant/

The GitHub Pages app is a Portuguese document Q&A desk. Offline it uses an embedded demo corpus with lexical retrieval. With the local API running, connect to `http://localhost:8000` to upload PDFs and query via `/upload` and `/query`.

---

## 🎯 What this project demonstrates

| Skill | How it is applied here |
|-------|------------------------|
| **RAG pipeline** | PDF extraction, chunking, dense embeddings, vector retrieval |
| **Open-source LLM stack** | No OpenAI key required; sentence-transformers + optional local LLM |
| **Vector database** | ChromaDB as a dedicated Docker service |
| **Backend API** | FastAPI with `/upload`, `/query`, `/health`, `/reset` endpoints |
| **Containerization** | Dockerfile + Docker Compose for reproducible deployments |
| **Testing** | pytest suite covering upload, query, citations, and health |
| **CI/CD** | GitHub Actions: lint, tests, Docker build, GitHub Pages deploy |
| **Portfolio** | Interactive GitHub Pages desk UI (demo corpus + live API mode) |

---

## 🏗️ Architecture

```
PDF Upload → Text Extraction → Chunking → Embeddings → ChromaDB
                                               ↓
FastAPI /query → Semantic Search → Retrieved Context → Answer + Citations
```

---

## 🛠️ Tech Stack

- **Python 3.11**
- **FastAPI** + Uvicorn
- **ChromaDB** (vector store, Docker service)
- **sentence-transformers** (`all-MiniLM-L6-v2`) for embeddings
- **LangChain** for optional local LLM integration
- **pypdf** for PDF text extraction
- **pytest** + **httpx** for testing
- **Docker** + **Docker Compose**
- **GitHub Actions** for CI/CD

---

## 📁 Project Structure

```
rag-technical-assistant/
├── src/rag_technical_assistant/
│   ├── api.py              # FastAPI application
│   ├── ingestion.py        # PDF extraction and chunking
│   ├── retrieval.py        # ChromaDB + sentence-transformers
│   └── generation.py       # Answer generation with citations
├── tests/
│   ├── test_api.py         # Endpoint integration tests
│   └── test_ingestion.py   # Unit tests for chunking helpers
├── data/
│   ├── documents/          # Uploaded PDFs
│   └── chroma/             # ChromaDB persistence
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .github/workflows/ci.yml
├── index.html              # Interactive desk UI (GitHub Pages)
├── _config.yml             # Jekyll config for GitHub Pages
└── README.md
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (recommended)

```bash
git clone https://github.com/Brunnobach/rag-technical-assistant.git
cd rag-technical-assistant

docker compose up --build
```

The API is available at `http://localhost:8000` and ChromaDB at `http://localhost:8001`.

### Option 2: Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start a local ChromaDB server or set CHROMA_HOST=localhost / CHROMA_PORT=8001
uvicorn rag_technical_assistant.api:app --app-dir src --reload
```

---

## 📡 API Usage

### Health check

```bash
curl http://localhost:8000/health
```

### Upload a PDF

```bash
curl -X POST -F "file=@manual.pdf" http://localhost:8000/upload
```

Response:

```json
{
  "filename": "manual.pdf",
  "document": "manual.pdf",
  "chunks_indexed": 12
}
```

### Ask a question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the maximum operating pressure?", "top_k": 4}'
```

Response:

```json
{
  "answer": "Based on the retrieved technical documents...",
  "sources": [
    {
      "document": "manual.pdf",
      "chunk_index": 3,
      "page": 7,
      "text": "The maximum operating pressure is 25 bar...",
      "score": 0.9123
    }
  ]
}
```

### Reset the knowledge base

```bash
curl -X POST http://localhost:8000/reset
```

---

## ⚙️ Configuration

Environment variables (all optional, defaults shown):

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_HOST` | `localhost` | ChromaDB hostname |
| `CHROMA_PORT` | `8001` | ChromaDB port |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model name |
| `CHUNK_SIZE` | `500` | Words per chunk |
| `CHUNK_OVERLAP` | `100` | Overlapping words between chunks |
| `TOP_K` | `4` | Number of chunks retrieved per query |
| `USE_LOCAL_LLM` | `false` | Use a local model instead of template fallback |
| `DATA_DIR` | `./data` | Root directory for documents and ChromaDB |

---

## 🧪 Testing

```bash
pip install -r requirements.txt
pytest
```

The test suite runs fully in-process using FastAPI's `TestClient` and an in-memory ChromaDB client, so no Docker is required for CI.

---

## 🚀 CI/CD

The GitHub Actions workflow (`ci.yml`) runs on every push and pull request to `main`:

1. Installs Python dependencies
2. Lints the code with Ruff
3. Runs the pytest suite
4. Builds the Docker image
5. Deploys the GitHub Pages landing page

---

## 🔒 Secrets & API Keys

This project is intentionally designed to run **without any API keys or secrets**.

- Embeddings use `sentence-transformers`
- Vector store uses self-hosted ChromaDB
- Answer generation defaults to a deterministic, citation-aware fallback
- Optional local LLM integration is controlled by `USE_LOCAL_LLM` and `MODEL_PATH`

No OpenAI, Anthropic, or other proprietary keys are required.

---

## 💡 Example Use Cases

- Question-answering over engineering manuals
- Regulatory and technical standard knowledge bases
- Internal consultancy document retrieval
- Plant operations and maintenance documentation assistants

---

## 🤝 Connect

Built by [Brunno Bachmann](https://www.linkedin.com/in/brunno-bachmann-865429173) as part of a portfolio transition into **Solutions Architect** and **Applied AI** roles in the DACH region.

---

## 📄 License

MIT
