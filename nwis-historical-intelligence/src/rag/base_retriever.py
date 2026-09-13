"""
Base retriever interface for NWIS RAG pipeline.
Defines the common retrieval abstraction implemented by both InMemory
and PostgreSQL + pgvector backends.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .embeddings import EmbeddingProvider


class BaseRetriever(ABC):
    """
    Abstract base class for RAG retrievers.
    Coordinates query embedding, candidate matching, and hybrid scoring.
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        provider: EmbeddingProvider,
        current_depth: Optional[float] = None,
        formation: Optional[str] = None,
        depth_tolerance: float = 100.0,
        event_type: Optional[str] = None,
        nearby_well_ids: Optional[list[str]] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Execute hybrid retrieval across indexed historical documents.

        Args:
            query (str): Natural language query string.
            provider (EmbeddingProvider): Embedding provider for query vectorization.
            current_depth (float, optional): Target drilling depth in meters.
            formation (str, optional): Target geological formation name.
            depth_tolerance (float): Depth window (+/-) in meters.
            event_type (str, optional): Target drilling event / incident type.
            nearby_well_ids (list[str], optional): Nearby offset well IDs.
            top_k (int): Maximum number of ranked results to return.

        Returns:
            list[dict]: Ranked results containing 'text', 'metadata',
                        'semantic_similarity', 'structured_score', and 'hybrid_score'.
        """
        pass
