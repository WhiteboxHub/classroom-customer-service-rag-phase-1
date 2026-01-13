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

### 3. Access Application

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
│   │   │   └── chat.py              # Chat API with RAG logic
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── scrapers.py      # Web scraping
│   │   │   │   ├── docling_processor.py  # Document processing
│   │   │   │   └── orchestrator.py  # Ingestion pipeline
│   │   │   ├── chunking/
│   │   │   │   └── semantic.py      # Semantic chunking
│   │   │   ├── generation/
│   │   │   │   └── embeddings.py    # Local embeddings
│   │   │   └── retrieval/
│   │   │       └── vector_store/
│   │   │           └── milvus.py    # Milvus client
│   ├── trigger_ingest.py            # Main ingestion script
│   └── Dockerfile
├── resources/
│   ├── source_docs/                 # All documents
│   └── models.yaml                  # Available LLM models
├── docker-compose.yml
└── .env                             # Configuration
```

---

## 🔄 Data Ingestion

### Supported File Types

- PDF (`.pdf`) - via Docling
- HTML (`.html`) - via Docling
- Text (`.txt`) - direct read
- JSON (`.json`) - direct parse
- DOCX (`.docx`) - via Docling

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

# Test API
curl http://localhost:8000/v1/models
```

### Test Queries

Try these questions to verify the system:

1. **Simple Query**: "What is Kaiser Permanente?"
2. **Document-Specific**: "What are provider responsibilities?"
3. **Web Content**: "Tell me about community providers"
4. **Out-of-Scope**: "What is the weather?" (should say "I don't know")

### Performance Metrics

- **Query Latency**: ~1.5-2.5 seconds
- **Embedding**: ~50ms (local)
- **Vector Search**: ~100ms
- **LLM Generation**: ~1-2s

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

| Source Type | Files | Chunks | Status |
|-------------|-------|--------|--------|
| PDF | 2 | ~2,051 | ✅ |
| HTML | 1 | 43 | ✅ |
| Text | 2 | 10 | ✅ |
| **Total** | **5** | **~2,104** | **✅** |

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

Potential enhancements:

1. **Real Confluence Integration**
2. **Advanced Chunking** (hierarchical/sliding window)
3. **Metadata Enrichment** (dates, authors, sections)
4. **Hybrid Search** (vector + keyword)
5. **Re-ranking** (cross-encoder)
6. **Monitoring** (Prometheus, Grafana)
7. **Authentication** (secure API/UI)
8. **Multi-tenancy**
9. **Incremental Updates**
10. **Analytics Dashboard**

---

## 📝 License & Credits

- **Docling**: IBM Research
- **sentence-transformers**: UKPLab
- **Milvus**: Zilliz
- **Groq**: Groq Inc.
- **Open-WebUI**: Open-WebUI Team

---

## 📞 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`
3. Review this README


