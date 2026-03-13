import asyncio
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.retrieval.neo4j_retriever import Neo4jRetriever

async def test_pipeline():
    print("=== Testing GraphRAG Pipeline ===")
    
    # 1. Initialize Orchestrator (this also initializes the Neo4j schema)
    orchestrator = IngestionOrchestrator()
    
    # 2. Dummy content to ingest
    sample_text = (
        "OpenAI created a system called GPT. GPT uses transformer technology "
        "to assist customers. John Doe works at OpenAI."
    )
    metadata = {"id": "test_doc_001"}
    
    print("\n--- 1. Ingesting Document ---")
    await orchestrator.ingest_document(metadata, sample_text)
    
    print("\n--- 2. Testing Retrieval ---")
    retriever = Neo4jRetriever()
    
    query = "Who works at OpenAI and what did they create?"
    results = retriever.retrieve_context(query, top_k=2)
    
    print("\n=== Hybrid Retrieval Results ===")
    print(f"Chunks found: {len(results['chunks'])}")
    for i, chunk in enumerate(results['chunks'], 1):
        print(f"  {i}. {chunk}")
        
    print(f"\nEntities found: {len(results['entities'])}")
    for ent in results['entities']:
        print(f"  - {ent['name']} ({ent['type']})")
        
    print(f"\nRelationships found: {len(results['relationships'])}")
    for rel in results['relationships']:
        print(f"  - ({rel['source']}) -[{rel['relation']}]-> ({rel['target']})")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
