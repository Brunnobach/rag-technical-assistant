# RAG Technical Assistant

**RAG-based AI assistant for technical documents**

Upload PDFs, ask questions and get answers grounded in your documents with cited sources.

---

## 🌐 Live Portfolio

🌐 **Landing page and demo:** https://brunnobach.github.io/rag-technical-assistant/

---

## 🎯 What this project demonstrates

| Skill | How it is applied here |
|-------|------------------------|
| **RAG (Retrieval-Augmented Generation)** | Document chunking, embeddings, vector search |
| **LLMs** | Answer generation with source citations |
| **Vector databases** | ChromaDB / Pinecone for semantic search |
| **Backend API** | FastAPI for upload and chat |
| **Frontend** | Simple web interface for demos |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PDF Upload  │────▶│   Chunking   │────▶│  Embeddings  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Chat UI/API │◀────│   Vector DB  │◀────│  LLM Answer  │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 🛠️ Tech Stack

- Python 3.10+
- LangChain / LlamaIndex
- ChromaDB
- OpenAI / Anthropic / Ollama
- FastAPI
- Streamlit (optional UI)
- Docker

---

## 📁 Project Structure

```
rag-technical-assistant/
├── data/
│   └── documents/        # PDFs and technical documents
├── src/
│   ├── ingestion/        # Load, chunk and embed documents
│   ├── retrieval/        # Vector search and context assembly
│   ├── generation/       # LLM answer generation
│   └── api/              # FastAPI app
├── app.py                # Streamlit UI
├── tests/                # Unit tests
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/Brunnobach/rag-technical-assistant.git
cd rag-technical-assistant

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Add PDFs to data/documents/

# Ingest documents
python src/ingestion/ingest.py

# Run API
python src/api/app.py

# Or run Streamlit UI
streamlit run app.py
```

---

## 💡 Example Use Cases

- Ask questions about biogas engineering manuals
- Query technical standards and regulations
- Build a knowledge base for a consultancy or plant

---

## 🤝 Connect

Built by [Brunno Bachmann](https://www.linkedin.com/in/brunno-bachmann-865429173) as part of a portfolio transition into Applied AI and RAG systems.

---

## 📄 License

MIT
