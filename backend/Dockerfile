FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency metadata
COPY pyproject.toml .

# Install dependencies ONLY (no packaging)
RUN pip install --no-cache-dir \
    fastapi>=0.100.0 \
    uvicorn>=0.23.0 \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    requests>=2.31.0 \
    celery>=5.3.0 \
    redis>=5.0.0 \
    pyyaml>=6.0 \
    pymilvus>=2.3.0 \
    pypdf>=3.0.0 \
    openai>=1.0.0 \
    tiktoken>=0.5.0 \
    selenium>=4.0.0 \
    beautifulsoup4>=4.0.0 \
    docling \
    sentence-transformers

# Copy app code
COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
