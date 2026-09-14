"""
RAG Retrieval Service coordinating historical events, document building,
vector embedding, in-memory semantic indexing, and hybrid retrieval.
Decoupled from LLM answer generation, dashboard UI, and persistent storage.
"""

from typing import Optional

from .base_retriever import BaseRetriever
from .document_builder import events_to_documents
from .embeddings import EmbeddingProvider, embed_documents
from .hybrid_retrieval import HybridRetriever
from .pgvector_backend import PgVectorRetriever, PgVectorDatabaseClient, ingest_events_to_pgvector
from .semantic_search import InMemorySemanticIndex


class RAGRetrievalService:
    """
    Coordinates historical events, document building, vector embedding,
    in-memory indexing, pgvector database indexing, and hybrid retrieval.
    """

    def __init__(
        self,
        events: Optional[list[dict]] = None,
        provider: Optional[EmbeddingProvider] = None,
        auto_prepare: bool = False,
        backend: str = "in_memory",
        retriever: Optional[BaseRetriever] = None,
        db_client: Optional[PgVectorDatabaseClient] = None,
    ):
        """
        Initialize the RAGRetrievalService.

        Args:
            events (list[dict], optional): Historical drilling events.
            provider (EmbeddingProvider, optional): Vector embedding provider.
            auto_prepare (bool): If True, prepares documents and index immediately.
            backend (str): Retrieval backend: "in_memory" (default) or "pgvector".
            retriever (BaseRetriever, optional): Pre-instantiated custom retriever.
            db_client (PgVectorDatabaseClient, optional): Database client for pgvector backend.
        """
        self.events = list(events) if events else []
        self.provider = provider
        self.backend = backend
        self.db_client = db_client
        self._is_prepared = False
        self._documents: list[dict] = []
        self._embedded_documents: list[dict] = []
        self._index: Optional[InMemorySemanticIndex] = None
        self._retriever: Optional[BaseRetriever] = retriever

        if self._retriever is not None:
            self._is_prepared = True
        elif self.backend == "pgvector":
            self._retriever = PgVectorRetriever(db_client=self.db_client)
            self._is_prepared = True

        if auto_prepare and not self._is_prepared:
            self.prepare()

    @property
    def is_prepared(self) -> bool:
        """Returns True if documents have been prepared, embedded, and indexed."""
        return self._is_prepared

    def prepare(self) -> None:
        """
        Prepares documents, generates embeddings once, builds semantic index,
        and initializes HybridRetriever.
        Safe to call multiple times (no-op if already prepared).
        """
        if self._is_prepared:
            return

        if not self.events:
            self._documents = []
            self._embedded_documents = []
            self._index = InMemorySemanticIndex()
            self._retriever = HybridRetriever(documents=[], index=self._index)
            self._is_prepared = True
            return

        # Check if events are already document dictionaries with embeddings
        if "text" in self.events[0] and "embedding" in self.events[0]:
            self._documents = self.events
            self._embedded_documents = self.events
        else:
            # 1. Convert events to document dicts
            self._documents = events_to_documents(self.events)

            # 2. Generate embeddings once using provider
            self._embedded_documents = embed_documents(self._documents, self.provider)

        # 3. Build in-memory semantic index
        self._index = InMemorySemanticIndex()
        self._index.add_documents(self._embedded_documents)

        # 4. Initialize HybridRetriever
        self._retriever = HybridRetriever(
            documents=self._embedded_documents,
            index=self._index,
        )
        self._is_prepared = True

    def retrieve(
        self,
        query: str,
        current_depth: Optional[float] = None,
        formation: Optional[str] = None,
        depth_tolerance: float = 100.0,
        event_type: Optional[str] = None,
        nearby_well_ids: Optional[list[str]] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Execute hybrid retrieval across prepared historical documents.
        Explicitly prepares if prepare() was not previously called.

        Args:
            query (str): Natural language search query.
            current_depth (float, optional): Drilling depth in meters.
            formation (str, optional): Geological formation name.
            depth_tolerance (float): Depth window tolerance (+/-) in meters.
            event_type (str, optional): Incident/event type name.
            nearby_well_ids (list[str], optional): List of nearby offset well IDs.
            top_k (int): Number of top results to return.

        Returns:
            list[dict]: Ranked evidence documents containing text, metadata,
                        semantic_similarity, structured_score, and hybrid_score.
        """
        if not self._is_prepared:
            self.prepare()

        if not self._retriever:
            return []

        return self._retriever.retrieve(
            query=query,
            provider=self.provider,
            current_depth=current_depth,
            formation=formation,
            depth_tolerance=depth_tolerance,
            event_type=event_type,
            nearby_well_ids=nearby_well_ids,
            top_k=top_k,
        )

    def ingest_to_db(
        self,
        db_client: Optional[PgVectorDatabaseClient] = None,
        batch_size: int = 50,
    ) -> int:
        """
        Generic data ingestion path into PostgreSQL + pgvector:
        events -> document_builder -> embedding provider -> PostgreSQL historical_event_embeddings

        Args:
            db_client (PgVectorDatabaseClient, optional): Database client instance.
            batch_size (int): Batch size for generating document embeddings.

        Returns:
            int: Number of records embedded and ingested.
        """
        if not self.events:
            return 0
        if not self.provider:
            raise ValueError("An EmbeddingProvider is required to ingest events into the database.")

        client = db_client or self.db_client or PgVectorDatabaseClient()
        return ingest_events_to_pgvector(
            events=self.events,
            provider=self.provider,
            db_client=client,
            batch_size=batch_size,
        )

