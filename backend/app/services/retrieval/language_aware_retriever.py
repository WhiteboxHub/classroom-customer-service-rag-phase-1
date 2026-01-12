from typing import List, Optional
from app.services.retrieval.vector_store.milvus import MilvusClient
from app.core.config import settings


class LanguageAwareRetriever:
    """
    Retrieval strategy layer.

    Implements:
    1. Same-language retrieval (preferred)
    2. Fallback to cross-language retrieval

    Storage-agnostic by design.
    """

    def __init__(self):
        self.vector_store = MilvusClient()

    async def retrieve(
        self,
        query_vector: List[float],
        limit: int = 5,
        language: Optional[str] = None,
    ) -> List[str]:
        """
        Retrieve documents with language-aware fallback.
        """

        # Try same-language retrieval if enabled
        if settings.ENABLE_LANGUAGE_FILTERING and language:
            results = await self.vector_store.search(
                query_vector=query_vector,
                limit=limit,
                language=language,
            )

            if results:
                return results

        # Fallback: retrieve from all languages
        return await self.vector_store.search(
            query_vector=query_vector,
            limit=limit,
            language=None,
        )
