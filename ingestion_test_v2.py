import asyncio
import os
import sys

# Simplified path logic for running from within the project folder
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")

if os.path.exists(backend_dir):
    sys.path.append(backend_dir)
else:
    print(f"Error: Could not find backend directory at {backend_dir}")
    sys.exit(1)

from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.retrieval.vector_store.milvus import MilvusClient
from app.services.generation.embeddings import EmbeddingService

async def test_ingestion():
    print("--- 1. Initializing Services ---")
    
    # Force localhost if running outside Docker
    os.environ["MILVUS_HOST"] = "localhost"
    os.environ["MILVUS_PORT"] = "19530"
    
    import socket
    import time
    
    def wait_for_milvus(host, port, retries=15, delay=3):
        print(f"Checking if Milvus is reachable at {host}:{port}...")
        for i in range(retries):
            try:
                with socket.create_connection((host, int(port)), timeout=2):
                    print("Milvus port is open!")
                    return True
            except:
                print(f"Milvus not reachable (attempt {i+1}/{retries})...")
                time.sleep(delay)
        return False

    if not wait_for_milvus("localhost", 19530):
        print("Error: Milvus is not reachable on localhost:19530. Ensure 'docker-compose up -d' was successful.")
        return

    orchestrator = IngestionOrchestrator()
    vector_store = MilvusClient()
    embedder = EmbeddingService()
    
    # Path to a sample file (PDF Manual for structural test)
    sample_file = os.path.join(current_dir, "resources", "source_docs", "kp-northern-ca-hmo-provider-manual.pdf")
    
    if not os.path.exists(sample_file):
        print(f"Error: Sample file not found at {sample_file}")
        return

    print(f"\n--- 2. Ingesting File: {os.path.basename(sample_file)} (Tenant: test_classroom_tenant) ---")
    # Testing with a specific tenant
    tenant_id = "test_classroom_tenant"
    success = await orchestrator.ingest_file(sample_file, tenant_id=tenant_id)
    
    if success:
        print("\n--- 3. Verifying Ingestion in Milvus ---")
        # Let's search for a query that would benefit from structural context
        query = "What are the rules for provider disputes?"
        query_vector = embedder.get_embedding(query, is_query=True)
        
        # Search specifically for the tenant we just ingested
        results = await vector_store.search(query_vector, limit=3, tenant_id=tenant_id)
        
        print(f"\nSearch results for '{query}' (Tenant: {tenant_id}):")
        if not results:
            print("No results found. Verification failed.")
        for i, res in enumerate(results):
            print(f"\n[Result {i+1}]")
            print(f"Content Snippet: {res[:200]}...")
            
        print("\n--- Ingestion Test Completed Successfully ---")
    else:
        print("\nIngestion failed.")

if __name__ == "__main__":
    asyncio.run(test_ingestion())
