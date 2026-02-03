# RAG Phase 1 - Kaiser Customer Service Assistant

A complete Retrieval Augmented Generation (RAG) system for Kaiser Permanente customer service, featuring multi-source data ingestion, local embeddings, and dual LLM provider support (Groq/OpenAI).

---

## 🎯 Overview

This RAG system helps customer service agents quickly find accurate information from multiple knowledge sources including PDFs, web pages, and text documents.

### Key Features

✅ **Multi-Source Ingestion**: PDFs, HTML, Text files, JSON  
✅ **Web Scraping**: Selenium + BeautifulSoup for dynamic content  
✅ **Local Embeddings**: sentence-transformers (no API costs)  
✅ **Dual LLM Support**: Groq (default) or OpenAI  
✅ **Vector Search**: Milvus for fast retrieval  
✅ **Modern UI**: Open-WebUI chat interface  
✅ **Production Ready**: Docker containerized  

---

## 🏗️ Architecture

```
User → Open-WebUI → FastAPI Backend → [Embeddings + Milvus + LLM] → Response
```

### Components

- **Open-WebUI** (Port 8080): Chat interface
- **FastAPI Backend** (Port 8000): RAG logic
- **Milvus**: Vector database for semantic search
- **PostgreSQL**: Metadata storage
- **Redis**: Caching
- **Groq/OpenAI**: LLM providers

### Data Flow

1. **Ingestion**: Web scraping → Docling processing → Chunking → Embedding → Milvus
2. **Query**: User question → Embed → Vector search → Context retrieval → LLM → Answer

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Internet connection (for first-time model downloads)

### 1. Start Services

```bash
cd classroom-customer-service-rag-phase-1
docker-compose up -d
```

### 2. First Startup (Includes Automatic Ingestion)

```bash
docker-compose up -d
```

**What happens automatically**:
- ✅ All services start (Backend, Milvus, PostgreSQL, Redis, Open-WebUI)
- ✅ **Ingestion runs automatically** (scrapes web content, processes PDFs)
- ✅ ~2,100 chunks embedded and stored in Milvus
- ⏱️ Takes ~5 minutes on first run

**Check ingestion progress**:
```bash
docker-compose logs -f ingestion
```

**Note**: Ingestion only runs on first startup. Data persists in Milvus between restarts.

### 4. Access Application

**Open-WebUI**: http://localhost:8080

1. Create an account (first user becomes admin)
2. Select model: `llama-3.3-70b-versatile`
3. Start asking questions!

### Example Questions

```
- What are the provider responsibilities?
- Tell me about community providers
- Explain the contracting process
- What information is in the HMO manual?
```

---

## ⚙️ Configuration

### LLM Provider Setup

The system supports both **Groq** (default) and **OpenAI**.

#### Using Groq (Default)

```bash
# .env file
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

#### Using OpenAI

```bash
# .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

#### Switch Between Providers

1. Edit `.env` file
2. Restart backend: `docker-compose restart backend`
3. Select appropriate model in UI

**Available Models:**

- **Groq**: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`

The system automatically routes to the correct API based on selected model!

### Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=groq                    # "groq" or "openai"
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag_app

# Vector Database
MILVUS_HOST=milvus
MILVUS_PORT=19530
```

---

## 📂 Project Structure

```
classroom-customer-service-rag-phase-1/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── chat.py              # Chat API with Tenant-Isolated search
│   │   │   └── ingest.py            # Async ingestion endpoints
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── scrapers.py      # Web scraping (Selenium)
│   │   │   │   ├── docling_processor.py  # IBM Docling integration
│   │   │   │   └── orchestrator.py  # Metadata & Ingestion Orchestration
│   │   │   ├── chunking/
│   │   │   │   └── semantic.py      # Docling HybridChunker (Structure-aware)
│   │   │   ├── generation/
│   │   │   │   └── embeddings.py    # E5-Base-V2 (768D) Implementation
│   │   │   └── retrieval/
│   │   │       └── vector_store/
│   │   │           └── milvus.py    # Milvus 768D with Metadata schemas
│   ├── trigger_ingest.py            # Main ingestion script
│   └── Dockerfile
├── resources/
│   ├── source_docs/                 # All documents
│   └── models.yaml                  # Available LLM models
├── ingestion_test_v2.py             # Metadata & Ingestion validation script
├── docker-compose.yml
└── .env                             # Configuration
```

---

## 🔄 Data Ingestion & Processing

### Supported File Types

- PDF (`.pdf`) - via Docling
- HTML (`.html`) - via Docling
- Text (`.txt`) - direct read
- JSON (`.json`) - direct parse
- DOCX (`.docx`) - via Docling

### The Metadata Collection Layer
In Phase 1, we implemented a dedicated layer to track:
- **Document Identity**: Unique IDs across system boundaries.
- **Multi-tenancy**: Mandatory `tenant_id` for every chunk.
- **Lifecycle State**: `last_modified` and `version` tracking.
- **Access Control**: Role-based permissions stored at the vector level.

### Docling Structure-Aware Chunking
We use **IBM Docling** to drive our chunking strategy:
- **Table Integrity**: Tables are extracted as structured objects, preserving row/column relationships.
- **Hierarchical Context**: Chunks respect section boundaries (headings, sub-headings).
- **Hybrid Strategy**: Combines structural parsing with semantic token-based grouping.

### Embedding Model: intfloat/e5-base-v2
- **Vector Size**: 768 dimensions.
- **Instructed Retrieval**: Uses `query: ` and `passage: ` prefixes for state-of-the-art accuracy.
- **Efficiency**: CPU/GPU (MPS) optimized for local deployment.

### Ingestion Pipeline

The `trigger_ingest.py` script:

1. **Scrapes** web content (HTML/Text)
2. **Saves** to `resources/source_docs/`
3. **Processes** all files with Docling
4. **Chunks** content semantically
5. **Embeds** using local sentence-transformers
6. **Stores** in Milvus vector database

### Add New Documents

1. Place files in `resources/source_docs/`
2. Run: `python3 backend/trigger_ingest.py`

### Add New Web Sources

Edit `backend/trigger_ingest.py`:

```python
# Add new scraping
scraper.scrape_html("https://your-url.com", "output.html")
scraper.scrape_text("https://your-url.com", "output.txt")
```

---

## 🧪 Testing

### Verify Services

```bash
# Check all services running
docker-compose ps

# Check backend logs
docker-compose logs -f backend
```

### Performance Benchmarks (Phase 1)

- **Vector Lookup**: < 150ms (Milvus 768D IVF_FLAT)
- **Metadata Filtering**: Instant (Scalar Indexing)
- **Table Retrieval**: High Accuracy (Docling Contextual Chunks)

---

## 🛠️ Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart backend
docker-compose restart backend

# View logs
docker-compose logs -f backend

# View ingestion logs
docker-compose logs -f ingestion

# Manually re-run ingestion (if you add new documents)
docker-compose restart ingestion

# Check Milvus data
docker-compose logs milvus

# Rebuild after code changes
docker-compose build backend
docker-compose up -d backend
```

---

## 📊 System Status

### Ingested Data

| Source Type | Processor | Chunks | Metadata Layer |
|-------------|-----------|--------|----------------|
| PDF | Docling | Struct-Aware | ✅ Active |
| HTML | Docling | Struct-Aware | ✅ Active |
| Text | Custom | Semantic | ✅ Active |
| JSON | Stringify | Structured | ✅ Active |

### Available Models

| Provider | Model | Speed | Quality | Cost |
|----------|-------|-------|---------|------|
| Groq | llama-3.3-70b-versatile | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰 |
| Groq | llama-3.1-8b-instant | ⚡⚡⚡⚡ | ⭐⭐⭐ | 💰 |
| OpenAI | gpt-4o | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 |
| OpenAI | gpt-4o-mini | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰💰 |
| OpenAI | gpt-3.5-turbo | ⚡⚡⚡ | ⭐⭐⭐ | 💰💰 |

---

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check Docker
docker --version
docker-compose --version

# Check logs
docker-compose logs

# Restart everything
docker-compose down
docker-compose up -d
```

### No Results from Queries

```bash
# Verify data ingestion
python3 backend/trigger_ingest.py

# Check Milvus
docker-compose logs milvus

# Restart backend
docker-compose restart backend
```

### API Key Errors

```bash
# Check .env file has correct keys
cat .env | grep API_KEY

# Verify provider setting
cat .env | grep LLM_PROVIDER

# Restart backend
docker-compose restart backend
```

### Slow Responses

- Try smaller model: `llama-3.1-8b-instant`
- Check Groq API status
- Reduce context chunks in `chat.py` (limit=3 → limit=2)

---

## 🔐 Security

⚠️ **Important**:

- Never commit API keys to version control
- Use `.env` file (already in `.gitignore`)
- Rotate keys regularly
- Use different keys for dev/prod
- Monitor API usage

---

## 📈 Performance Optimization

### For Development
- Use `llama-3.1-8b-instant` (fast iteration)
- Lower cost, quick responses

### For Production
- Use `llama-3.3-70b-versatile` (best balance)
- Or `gpt-4o-mini` if using OpenAI

### For Maximum Quality
- Use `gpt-4o` when accuracy is critical
- Higher cost but best results

---

## 🚀 Next Steps (Phase 2+)

1. **Real Confluence Integration**
2. **PostgreSQL Relational Metadata Sync** (Synchronizing vector fields with persistent SQL tables)
3. **Hybrid Search** (vector + keyword functionality)
4. **Re-ranking** (Cross-encoder integration)
5. **Observability** (Prometheus, Grafana for retrieval metrics)
6. **Incremental Document Updates** (upsert based on version tags)
7. **Analytics Dashboard**

---

## 📝 License & Credits

- **Docling**: IBM Research
- **sentence-transformers**: UKPLab
- **Milvus**: Zilliz
- **Groq**: Groq Inc.
- **Open-WebUI**: Open-WebUI Team

---

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`


