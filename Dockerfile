FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for scientific / ML packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the default embedding model so the container starts quickly
RUN python -c \
    "from sentence_transformers import SentenceTransformer; \
     SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY src/ ./src/

# Create data directories
RUN mkdir -p /app/data/documents /app/data/chroma

ENV PYTHONPATH=/app/src
ENV DATA_DIR=/app/data
ENV CHROMA_DIR=/app/data/chroma
ENV DOCS_DIR=/app/data/documents
ENV USE_LOCAL_LLM=false

EXPOSE 8000

CMD ["uvicorn", "rag_technical_assistant.api:app", "--host", "0.0.0.0", "--port", "8000"]
