import asyncio
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.retrieval.neo4j_retriever import Neo4jRetriever
from app.services.embeddings.embedding_model import EmbeddingModel
from app.services.database.neo4j_client import get_neo4j_client

async def compare_retrieval():
    print("=== Ingesting Sample Data for Comparison ===")
    orchestrator = IngestionOrchestrator()
    
    # We ingest a complex document demonstrating entities and relations
    sample_text = (
        "Acme Corp released a new product called the SuperWidget. "
        "Alice Smith is the CEO of Acme Corp and she works in London. "
        "The SuperWidget requires a power supply to operate."
    )
    metadata = {"id": "doc_comparison_001"}
    
    await orchestrator.ingest_document(metadata, sample_text)
    print("Ingestion complete.\n")

    query = "Who is the CEO of Acme Corp and what product did they release?"
    
    print(f"QUERY: '{query}'\n")

    # 1. Standard RAG (Pure Vector Search on Chunks)
    print("=== Method 1: Standard RAG (Vector Search Only) ===")
    embedder = EmbeddingModel()
    client = get_neo4j_client()
    query_embedding = embedder.embed(query)
    
    vector_search_cypher = """
    CALL db.index.vector.queryNodes('chunk_embedding_index', 2, $query_embedding)
    YIELD node AS c, score
    RETURN c.text AS text, score
    """
    
    standard_results = client.run(vector_search_cypher, query_embedding=query_embedding)
    for i, res in enumerate(standard_results, 1):
        print(f"Chunk {i} (Score: {res['score']:.4f}):\n{res['text']}\n")

    print("-" * 50)
    
    # 2. GraphRAG (Hybrid Search with Ontology and Relationships)
    print("=== Method 2: GraphRAG (Hybrid Search) ===")
    retriever = Neo4jRetriever()
    hybrid_results = retriever.retrieve_context(query, top_k=2)
    
    print("--- Retrieved Chunks ---")
    for i, chunk in enumerate(hybrid_results['chunks'], 1):
        print(f"Chunk {i}:\n{chunk}")
        
    print("\n--- Retrieved Concept Entities (Ontology-driven) ---")
    for ent in hybrid_results['entities']:
        print(f"- {ent['name']} (Type: {ent['type']})")
        
    print("\n--- Retrieved Relationships (Graph Traversal) ---")
    for rel in hybrid_results['relationships']:
        print(f"- ({rel['source']}) -> [{rel['relation']}] -> ({rel['target']})")
        
    print("\nNotice how Method 2 pulls back structural data (who works where, what was released) "
          "that an LLM can use to perfectly answer the prompt without hallucinating.")

if __name__ == "__main__":
    asyncio.run(compare_retrieval())
