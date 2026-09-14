from .base_retriever import BaseRetriever
from .document_builder import event_to_document, events_to_documents
from .embeddings import EmbeddingProvider, GeminiEmbeddingProvider, embed_documents
from .semantic_search import cosine_similarity, InMemorySemanticIndex
from .hybrid_retrieval import HybridRetriever, InMemoryRetriever, compute_structured_score
from .pgvector_backend import (
    PgVectorDatabaseClient,
    PgVectorRetriever,
    ingest_events_to_pgvector,
)
from .retrieval_service import RAGRetrievalService
from .context_builder import build_rag_context
from .answer_service import RAGAnswerService

__all__ = [
    "event_to_document",
    "events_to_documents",
    "EmbeddingProvider",
    "GeminiEmbeddingProvider",
    "embed_documents",
    "cosine_similarity",
    "InMemorySemanticIndex",
    "BaseRetriever",
    "HybridRetriever",
    "InMemoryRetriever",
    "PgVectorRetriever",
    "PgVectorDatabaseClient",
    "ingest_events_to_pgvector",
    "compute_structured_score",
    "RAGRetrievalService",
    "build_rag_context",
    "RAGAnswerService",
]

