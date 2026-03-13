# Classroom Customer Service RAG - Phase 1

**Kaiser Customer Call Center Agent (Enterprise GraphRAG Edition)**

This project implements Phase 1 of the Retrieval Augmented Generation (RAG) system for the Kaiser Customer Call Center. It provides agents with accurate, context-aware answers derived from internal documentation. 

This phase has been heavily re-architected from a standard Vector RAG pipeline to a **Production-Quality GraphRAG pipeline using Neo4j**, enabling strict ontology-driven entity extraction, dual node-level embeddings, and hybrid multi-strategy retrieval for maximum accuracy and multi-hop reasoning.

---

## 💡 Project Overview
Customer service agents often struggle to find the right information quickly across multiple disconnected knowledge bases. This project unifies these sources into a single advanced GraphRAG pipeline capable of reading documents, extracting medical and organizational entities according to a strict ontology, mapping their semantic relationships, and executing complex hybrid retrieval strategies to generate hallucination-free answers.

---

## 🏗 Architecture & Workflow

The system follows a microservices architecture orchestrated via Docker Compose, built entirely around the **Neo4j Graph Database**.

### Core Workflow (GraphRAG Pipeline)
1. **Ingestion & Chunking**: The `/api/v1/ingest` and `/api/v1/ingest/pdf` endpoints accept text or PDF files. Documents are parsed and safely chunked via the `SemanticChunker`.
2. **Ontology-Driven Extraction**: `spaCy` NLP automatically extracts nouns into a strict canon: `PERSON`, `ORGANIZATION`, `LOCATION`, `PRODUCT`, `TECHNOLOGY` (falling back to a generic `ENTITY` designation when necessary).
3. **Relation Normalization**: Using linguistic dependency parsing, the system maps structural verb relationships between extracted entities dynamically, falling back to a normalized `RELATED_TO` semantic bridge where linguistic verbs fail to map cleanly.
4. **Dual Node-Level Vector Embedding**: *Both* Chunks and individual Entities are explicitly converted into 384-dimensional dense vectors using `sentence-transformers` (`all-MiniLM-L6-v2`) prior to storage.
5. **Idempotent Graph Storage**: The Document metadata, text chunks, vectors, entities, and edges are written natively to **Neo4j** via strict `MERGE` constraints. No duplicates are created. The graph strictly enforces the pattern: `(Document)-[:HAS_CHUNK]->(Chunk)-[:MENTIONS]->(Entity)-[:RELATION]->(Entity)`.
6. **Hybrid Three-Stage Retrieval**: When a query hits `/api/v1/chat/completions`, the `Neo4jRetriever` combines:
   - **Semantic Search**: Parallel Cosine vector similarity across both Chunks *and* Entities.
   - **Keyword Search**: Native Neo4j Fulltext index matching across Text and Names.
   - **Graph Traversal**: Explicit multi-hop path expansion outwards from matched entities to discover bridging knowledge.
7. **Generation**: An LLM (via Groq or OpenAI) synthesizes an answer using the hyper-dense, deduplicated context dictionary.

---

## 🚀 Key AI/ML Upgrades
* **Strict Ontology Typing**: SPAcy outputs map securely to `PERSON`, `ORG`, `LOC`, `PRODUCT`, and `TECHNOLOGY` ensuring the LLM doesn't hallucinate definitions.
* **Granular Entity Embeddings**: Vector math runs against discrete entity strings natively using Neo4j Vector Indexes, not just massive vague text chunks.
* **Deduplicated Hybrid Search**: By blending Semantic, Full-text, and Navigational Graph Traversals, the retriever pulls back context a pure-vector Milvus database mathematically cannot see.
* **Idempotent Merging**: You can ingest the same document repeatedly and Neo4j will update properties rather than stacking redundant nodes.

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
│   │   │   └── retrieval/       # Hybrid Neo4j Vector + Graph retrieval
│   │   └── workers/        # Celery task definitions
│   ├── scripts/            # Maintenance scripts
│   └── tests/              # Pytest Unit tests with Dependency Mocking
├── open-webui/             # Frontend chat interface
├── gateway/                # Nginx Configuration
├── evaluation/             # RAGAS datasets & evaluation runners
├── observability/          # Prometheus & Grafana configs
├── docker-compose.yml      # Main stack definition
├── pyproject.toml          # Python project dependencies
├── compare_rag.py          # Testing script validating Hybrid GraphRAG superiority
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

---

## 📦 Dependencies

Defined in `backend/pyproject.toml`:
* **Core**: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
* **Graph & Data**: `neo4j`
* **NLP & Embeddings**: `spacy`, `sentence-transformers`, `torch`
* **File Processing**: `pypdf2`, `python-multipart`

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

1. **Testing Hybrid Retrieval Quality**:
   From your local backend virtual environment, execute the comparison script:
   ```bash
   $env:PYTHONPATH="backend"
   python compare_rag.py
   ```
   *Witness how the Graph traversal captures exact entities and relations a standard Vector Search completely misses.*

2. **Ingesting a PDF**:
   Head to `http://localhost:8000/docs`, expand `POST /api/v1/ingest/pdf`, click "Try it out", upload a PDF, and click Execute. The system will parse it, extract entities to ontology rules, embed the entities, and write idempotent graph edges securely!

3. **Viewing the Knowledge Graph**:
   Head to `http://localhost:7474`. Log in with `neo4j / password`. Run the Cypher query:
   ```cypher
   MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity) RETURN d, c, e LIMIT 300
   ```
   You will see an interactive map of text chunks securely linked to strict organizational concepts!
