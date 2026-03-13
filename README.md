# Classroom Customer Service RAG - Phase 1

**Kaiser Customer Call Center Agent (GraphRAG Edition)**

This project implements Phase 1 of the Retrieval Augmented Generation (RAG) system for the Kaiser Customer Call Center. It provides agents with accurate, context-aware answers derived from internal documentation. 

This phase has been upgraded from a standard Vector RAG pipeline to a **GraphRAG pipeline using Neo4j**, enabling deep entity relationships, context expansion, and more accurate multi-hop reasoning.

---

## 💡 Project Overview
Customer service agents often struggle to find the right information quickly across multiple disconnected knowledge bases. This project unifies these sources into a single GraphRAG pipeline capable of reading documents, extracting medical and organizational entities, understanding their relationships, and using an LLM to generate precise answers.

---

## 🏗 Architecture & Workflow

The system follows a microservices architecture orchestrated via Docker Compose.

### Core Workflow (GraphRAG Pipeline)
1. **Ingestion & Chunking**: The `/api/v1/ingest` and `/api/v1/ingest/pdf` endpoints accept text or PDF files. Documents are parsed and split into overlapping textual chunks using the `SemanticChunker`.
2. **Entity Extraction**: `spaCy` NLP automatically extracts nouns into canonical types: Person, Organization, Location, Product, System, and Concept.
3. **Relationship Extraction**: Using linguistic dependency parsing, the system draws verb-based relationships between the extracted entities (e.g., `(Alice)-[:WORKS_AT]->(Kaiser)`).
4. **Vector Embedding**: Each chunk is converted into a 384-dimensional dense vector using `sentence-transformers` (`all-MiniLM-L6-v2`).
5. **Graph Storage**: The text chunks, vectors, entities, and relationship edges are stored atomically in **Neo4j** (`graph_ingestion.py`).
6. **Two-Stage Retrieval**: When a query hits `/api/v1/chat/completions`:
   - **Vector Search**: Finds the closest matching chunks using Neo4j's vector index.
   - **Graph Expansion**: Traverses the graph from the winning chunks to find shared entities and pulls in neighboring chunks to broaden the LLM's context.
7. **Generation**: An LLM (via Groq or OpenAI) synthesizes an answer using the retrieved neighborhood.

---

## 🚀 Features Implemented
* Complete removal of Milvus in favor of **Neo4j Graph Database**.
* Automated natural language processing (NLP) using **spaCy**.
* Local, high-performance vector embeddings via **sentence-transformers**.
* PDF file upload and parsing using **PyPDF2**.
* FastAPI-based **background task workers** for immediate API responses during ingestion.
* A React-based **Open WebUI** for ChatGPT-like agent interactions.

---

## 🔌 API Endpoints
* `POST /api/v1/ingest`: Ingest raw text or load from S3 object keys.
* `POST /api/v1/ingest/pdf`: Upload and extract text directly from a `.pdf` file.
* `GET  /api/v1/ingest/{job_id}`: Check the status of a scheduled ingestion job.
* `POST /api/v1/chat/completions`: Submit an OpenAI-compatible chat payload to run the GraphRAG retrieval chain and get an AI response.
* `GET  /health`: Standard readiness check probe.

---

## 📂 Folder Structure

```text
.
├── backend/                # Core Application
│   ├── app/
│   │   ├── api/v1/         # Endpoints (chat, ingest, admin, etc.)
│   │   ├── core/           # Config & Environment variables
│   │   ├── services/       # GraphRAG logic modules
│   │   │   ├── chunking/        # Semantic text chunking
│   │   │   ├── database/        # Neo4j Client & Schema constraints
│   │   │   ├── embeddings/      # local sentence-transformers models
│   │   │   ├── generation/      # LLM answer synthesis
│   │   │   ├── ingestion/       # Graph write operations & Orchestrator
│   │   │   ├── preprocessing/   # spaCy Entity & Relationship NLP extractors
│   │   │   └── retrieval/       # Two-stage Vector + Graph retrieval
│   │   └── workers/        # Celery task definitions
│   ├── scripts/            # Maintenance scripts
│   └── tests/              # Pytest Unit tests with Dependency Mocking
├── open-webui/             # Frontend chat interface
├── gateway/                # Nginx Configuration
├── evaluation/             # RAGAS datasets & evaluation runners
├── observability/          # Prometheus & Grafana configs
├── docker-compose.yml      # Main stack definition
├── pyproject.toml          # Python project dependencies
└── README.md               # This documentation
```

---

## ⚙️ Configuration Variables

Defined in `backend/app/core/config.py` and configurable via the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Name of the Application | `"Classroom CS RAG"` |
| `ENVIRONMENT` | Running environment (dev, prod) | `"dev"` |
| `NEO4J_URI` | Neo4j Bolt Connection String | `"bolt://localhost:7687"` |
| `NEO4J_USER` | Neo4j Database Username | `"neo4j"` |
| `NEO4J_PASSWORD` | Neo4j Database Password | `"password"` |
| `EMBEDDING_MODEL` | HuggingFace model string | `"all-MiniLM-L6-v2"` |
| `EMBEDDING_DIM` | Dimensions of the vector | `384` |
| `LLM_PROVIDER` | `groq` or `openai` | `"groq"` |
| `GROQ_API_KEY` | Your Groq API Key | `""` |
| `OPENAI_API_KEY` | Your OpenAI API Key | `""` |
| `POSTGRES_USER` | Relational DB User | `"postgres"` |
| `POSTGRES_PASSWORD`| Relational DB Password | `"postgres"` |
| `POSTGRES_DB` | Relational DB Name | `"rag_app"` |

---

## 📦 Dependencies

Defined in `backend/pyproject.toml`:
* **Core**: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
* **Graph & Data**: `neo4j`
* **NLP & Embeddings**: `spacy`, `sentence-transformers`, `torch`
* **File Processing**: `pypdf2`, `python-multipart`
* **Testing**: `pytest`, `pytest-asyncio`

---

## 🚀 Setup Instructions

### Prerequisites
* Docker & Docker Compose
* Python 3.11+ (if running backend locally)

### 1. Configuration
Copy the template and fill in your secrets (OpenAI / Groq API Keys).
```bash
cp .env.example .env
```

### 2. Start the Stack
This spins up the NGINX Gateway, FastAPI Backend, Open WebUI Frontend, Neo4j Graph DB, and Redis.
```bash
docker-compose up -d --build
```

### 3. Access Interfaces
*   **Customer Chat UI**: [http://localhost:8080](http://localhost:8080) (Ensure no port conflicts on 8080).
*   **FastAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Neo4j Knowledge Graph UI**: [http://localhost:7474](http://localhost:7474)

---

## 📖 Example Usage

1. **Ingesting a PDF**:
   Head to `http://localhost:8000/docs`, expand `POST /api/v1/ingest/pdf`, click "Try it out", upload a PDF, and click Execute. The system will parse it, extract entities in the background, and load them into Neo4j.

2. **Viewing the Knowledge Graph**:
   Head to `http://localhost:7474`. Log in with `neo4j / password`. Run the Cypher query:
   ```cypher
   MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 300
   ```
   You will see an interactive map of text chunks securely linked to organizational concepts!

3. **Asking a Question**:
   Access the Open WebUI at `http://localhost:8080` (or `http://localhost:8085` if you altered your docker-compose file). Type natural language questions like *"What is the Kaiser Billing Policy?"* and receive AI answers infused with the Neo4j graph context.
