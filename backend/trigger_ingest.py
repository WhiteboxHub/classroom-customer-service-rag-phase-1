import asyncio
import os
import sys

# Add /app to pythonpath so imports work
sys.path.append("/app")

from app.services.ingestion.orchestrator import IngestionOrchestrator

async def main():
    print("Initializing ingestion orchestrator...")
    orchestrator = IngestionOrchestrator()
    
    file_path = "/resources/source_docs/RAG (Retrieval Augmented Generation) - Study Guide – Kaiser Customer Call Center Agent.pdf"
    
    print(f"Attempting to ingest: {file_path}")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at {file_path}")
        print(f"Listing /resources/source_docs:")
        try:
            print(os.listdir("/resources/source_docs"))
        except:
            print("Directory not found")
        return

    success = await orchestrator.ingest_file(file_path)
    if success:
        print("Ingestion COMPLETED successfully.")
    else:
        print("Ingestion FAILED.")

if __name__ == "__main__":
    asyncio.run(main())
