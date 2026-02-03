import asyncio
import os
import sys

# Add /app to pythonpath so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming backend/app structure
sys.path.append(os.path.join(current_dir, "app"))
sys.path.append(current_dir) # To be safe

from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.ingestion.scrapers import ScraperService
import time

async def wait_for_milvus(host="milvus", port="19530", retries=10, delay=5):
    import socket
    print(f"Waiting for Milvus at {host}:{port}...")
    for i in range(retries):
        try:
            with socket.create_connection((host, int(port)), timeout=2):
                print("Milvus is reachable!")
                # Give it an extra second for service initialization
                time.sleep(2)
                return True
        except (socket.timeout, ConnectionRefusedError):
            print(f"Milvus not ready yet (attempt {i+1}/{retries})...")
            time.sleep(delay)
    return False

async def main():
    print("Initializing ingestion pipeline...")
    
    # Ensure Milvus is ready
    milvus_host = os.getenv("MILVUS_HOST", "milvus")
    milvus_port = os.getenv("MILVUS_PORT", "19530")
    if not await wait_for_milvus(host=milvus_host, port=milvus_port):
        print("Error: Could not connect to Milvus. Exiting.")
        return
    
    # Define directories
    # Go up one level from backend/ to root, then resources/source_docs
    base_dir = os.path.dirname(current_dir)
    source_docs_dir = os.path.join(base_dir, "resources", "source_docs")
    
    print(f"Source Docs Directory: {source_docs_dir}")
    if not os.path.exists(source_docs_dir):
        os.makedirs(source_docs_dir)

    # 1. Scraping Step
    scraper = ScraperService(output_dir=source_docs_dir)
    
    # HTML Scraping
    html_url = "https://healthy.kaiserpermanente.org/northern-california/community-providers/provider-info"
    scraper.scrape_html(html_url, "provider-info.html")
    
    # Text Scraping
    text_url = "https://healthy.kaiserpermanente.org/community-providers/national-contracting/faq"
    scraper.scrape_text(text_url, "national-contracting-faq.txt")
    
    # Confluence Dummy
    scraper.fetch_confluence_docs()
    
    # 2. Ingestion Step (Docling + Chunking + Embedding + Storage)
    print("\nStarting Orchestrator for Ingestion...")
    orchestrator = IngestionOrchestrator()
    
    success = await orchestrator.ingest_directory(source_docs_dir)
    
    if success:
        print("\nPipeline COMPLETED successfully.")
    else:
        print("\nPipeline finished with some errors (check logs).")

if __name__ == "__main__":
    asyncio.run(main())
