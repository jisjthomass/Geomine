"""
PostgreSQL + pgvector retrieval backend for NWIS RAG pipeline.
Coordinates persistent vector search, strict structured filtering,
metric conversion from cosine distance to similarity, and hybrid ranking.
"""

from typing import Any, Callable, Dict, List, Optional
import numpy as np

from .base_retriever import BaseRetriever
from .document_builder import events_to_documents
from .embeddings import EmbeddingProvider, embed_documents
from .hybrid_retrieval import (
    SEMANTIC_WEIGHT,
    STRUCTURED_WEIGHT,
    compute_structured_score,
    filter_candidates,
)


class PgVectorDatabaseClient:
    """
    Database client interface for pgvector operations on historical_event_embeddings.
    Decoupled from raw query strings and SQL connection setup.
    """

    def __init__(self, db_module=None, connection_factory: Optional[Callable] = None):
        """
        Initialize client with either a db_module (such as rag.rag_db_module)
        or a custom connection factory callable.
        """
        self.db_module = db_module
        self.connection_factory = connection_factory

        if self.db_module is None and self.connection_factory is None:
            try:
                # Try importing the repository-level rag_db_module
                import rag.rag_db_module as default_db_module
                self.db_module = default_db_module
            except ImportError:
                try:
                    import rag_db_module as default_db_module
                    self.db_module = default_db_module
                except ImportError:
                    self.db_module = None

    def is_available(self) -> bool:
        """Checks if PostgreSQL database is reachable."""
        try:
            if self.connection_factory:
                conn = self.connection_factory()
                conn.close()
                return True
            elif self.db_module and hasattr(self.db_module, "get_db_connection"):
                conn = self.db_module.get_db_connection()
                conn.close()
                return True
        except Exception:
            return False
        return False

    def insert_event_embedding(
        self,
        event_id: int,
        content: str,
        embedding: List[float],
        well_id: Optional[str] = None,
        depth_m: Optional[float] = None,
        formation: Optional[str] = None,
        event_type: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> int:
        """
        Inserts an event document and its vector embedding into historical_event_embeddings.
        Returns the created record ID.
        """
        if not embedding or not isinstance(embedding, (list, tuple)):
            raise ValueError("Embedding must be a non-empty list or tuple of numbers.")
        if event_id is None or content is None:
            raise ValueError("event_id and content are required.")

        if self.db_module and hasattr(self.db_module, "insert_event_embedding"):
            return self.db_module.insert_event_embedding(
                event_id=event_id,
                content=content,
                embedding=embedding,
                well_id=well_id,
                depth_m=depth_m,
                formation=formation,
                event_type=event_type,
                report_id=report_id,
                document_type=document_type,
            )

        # Direct execution via connection factory
        if not self.connection_factory:
            raise RuntimeError("No database module or connection factory available.")

        conn = self.connection_factory()
        cursor = conn.cursor()
        try:
            embedding_str = f"[{','.join(map(str, embedding))}]"
            query = """
                INSERT INTO historical_event_embeddings 
                (event_id, content, embedding, well_id, depth_m, formation, event_type, report_id, document_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            cursor.execute(
                query,
                (event_id, content, embedding_str, well_id, depth_m, formation, event_type, report_id, document_type),
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def semantic_search(
        self,
        query_embedding: List[float],
        formation: Optional[str] = None,
        min_depth: Optional[float] = None,
        max_depth: Optional[float] = None,
        event_type: Optional[str] = None,
        nearby_well_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes vector search with optional structured filtering on PostgreSQL + pgvector.
        Returns a dictionary containing list of matching records with cosine distance.
        """
        if not query_embedding or not isinstance(query_embedding, (list, tuple)):
            raise ValueError("query_embedding must be a non-empty list or tuple of numbers.")
        if top_k is None or top_k < 1:
            top_k = 5

        if self.db_module and hasattr(self.db_module, "semantic_search"):
            return self.db_module.semantic_search(
                query_embedding=query_embedding,
                formation=formation,
                min_depth=min_depth,
                max_depth=max_depth,
                event_type=event_type,
                nearby_well_ids=nearby_well_ids,
                top_k=top_k,
            )

        if not self.connection_factory:
            raise RuntimeError("No database module or connection factory available.")

        conn = self.connection_factory()
        cursor = conn.cursor()
        try:
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            query = """
                SELECT 
                    event_id, content, well_id, depth_m, formation, event_type, report_id, document_type,
                    (embedding <=> %s::vector) AS distance
                FROM historical_event_embeddings
                WHERE 1=1
            """
            params: list = [embedding_str]

            if formation and formation.strip():
                query += " AND LOWER(formation) = LOWER(%s)"
                params.append(formation.strip())
            if min_depth is not None:
                query += " AND depth_m >= %s"
                params.append(float(min_depth))
            if max_depth is not None:
                query += " AND depth_m <= %s"
                params.append(float(max_depth))
            if event_type and event_type.strip():
                query += " AND LOWER(event_type) = LOWER(%s)"
                params.append(event_type.strip())
            if nearby_well_ids and len(nearby_well_ids) > 0:
                query += " AND well_id = ANY(%s)"
                params.append(list(nearby_well_ids))

            query += " ORDER BY distance ASC LIMIT %s;"
            params.append(top_k)

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append({
                    "event_id": row[0],
                    "content": row[1],
                    "well_id": row[2],
                    "depth_m": row[3],
                    "formation": row[4],
                    "event_type": row[5],
                    "report_id": row[6],
                    "document_type": row[7],
                    "distance": float(row[8]),
                })
            return {"results": results}
        finally:
            cursor.close()
            conn.close()


class PgVectorRetriever(BaseRetriever):
    """
    Production RAG retriever backed by PostgreSQL and the pgvector extension.
    Converts cosine distance to cosine similarity, evaluates structured score,
    and computes hybrid ranking identically to the in-memory retriever.
    """

    def __init__(
        self,
        db_client: Optional[PgVectorDatabaseClient] = None,
        candidate_multiplier: int = 5,
    ):
        """
        Initialize PgVectorRetriever.

        Args:
            db_client (PgVectorDatabaseClient, optional): Database client instance.
            candidate_multiplier (int): Multiplier for candidate retrieval before re-ranking.
        """
        self.db_client = db_client or PgVectorDatabaseClient()
        self.candidate_multiplier = max(1, candidate_multiplier)

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
        Execute hybrid retrieval via PostgreSQL + pgvector.

        1. Generates query embedding via provider.embed_text(query).
        2. Queries database candidates using cosine distance (<=>).
        3. Converts cosine distance to similarity: similarity = 1.0 - distance.
        4. Evaluates structured scoring using compute_structured_score.
        5. Computes hybrid score: 0.60 * semantic_norm + 0.40 * structured_score.
        6. Returns top_k results sorted descending by hybrid score.
        """
        if top_k <= 0 or not query:
            return []

        if provider is None or not hasattr(provider, "embed_text"):
            raise ValueError("A valid EmbeddingProvider instance is required.")

        # Check if structured constraints are present
        has_structured_constraints = bool(
            (formation is not None and bool(str(formation).strip()))
            or (current_depth is not None)
            or (event_type is not None and bool(str(event_type).strip()))
            or (nearby_well_ids is not None and len(nearby_well_ids) > 0)
        )

        min_depth = None
        max_depth = None
        if current_depth is not None:
            try:
                c_depth = float(current_depth)
                tol = float(depth_tolerance) if depth_tolerance is not None else 100.0
                min_depth = max(0.0, c_depth - tol)
                max_depth = c_depth + tol
            except (ValueError, TypeError):
                pass

        # Generate query embedding once
        query_embedding = provider.embed_text(query)
        if not query_embedding:
            return []

        candidate_limit = max(top_k * self.candidate_multiplier, 20)

        # Retrieve candidates from PostgreSQL
        if has_structured_constraints:
            # When structured constraints are active, query with those constraints
            resp = self.db_client.semantic_search(
                query_embedding=query_embedding,
                formation=formation,
                min_depth=min_depth,
                max_depth=max_depth,
                event_type=event_type,
                nearby_well_ids=nearby_well_ids,
                top_k=candidate_limit,
            )
            candidates = resp.get("results", [])

            # CRITICAL RULE: When explicit structured constraints exist and zero candidates
            # satisfy them, return empty candidates rather than unrelated unconstrained results.
            if not candidates:
                return []
        else:
            # Genuinely general semantic query without structured constraints
            resp = self.db_client.semantic_search(
                query_embedding=query_embedding,
                formation=None,
                min_depth=None,
                max_depth=None,
                event_type=None,
                nearby_well_ids=None,
                top_k=candidate_limit,
            )
            candidates = resp.get("results", [])

        if not candidates:
            return []

        # HARD FILTER ON CANDIDATES (Ensuring 100% parity across in-memory and PostgreSQL backends)
        if has_structured_constraints:
            candidates = filter_candidates(
                items=candidates,
                formation=formation,
                current_depth=current_depth,
                depth_tolerance=depth_tolerance,
                event_type=event_type,
                nearby_well_ids=nearby_well_ids,
            )
            if not candidates:
                return []

        # Perform hybrid scoring
        results = []
        for row in candidates:
            dist = float(row.get("distance", 1.0))
            # Metric Conversion:
            # pgvector cosine distance: d = 1 - cos(theta) in [0, 2]
            # Cosine similarity: s = 1 - d in [-1, 1]
            cos_sim = float(np.clip(1.0 - dist, -1.0, 1.0))

            # Semantic normalization to [0, 1]: (cos_sim + 1) / 2 = 1 - d / 2
            semantic_norm = float(np.clip((cos_sim + 1.0) / 2.0, 0.0, 1.0))

            metadata = {
                "event_id": row.get("event_id"),
                "well_id": row.get("well_id"),
                "depth_m": row.get("depth_m"),
                "formation": row.get("formation"),
                "event_type": row.get("event_type"),
                "report_id": row.get("report_id"),
                "document_type": row.get("document_type"),
            }

            s_score = compute_structured_score(
                metadata=metadata,
                formation=formation,
                current_depth=current_depth,
                depth_tolerance=depth_tolerance,
                event_type=event_type,
                nearby_well_ids=nearby_well_ids,
            )

            hybrid_score = float(SEMANTIC_WEIGHT * semantic_norm + STRUCTURED_WEIGHT * s_score)

            results.append({
                "text": row.get("content", ""),
                "metadata": metadata,
                "semantic_similarity": cos_sim,
                "distance": dist,
                "structured_score": s_score,
                "hybrid_score": hybrid_score,
            })

        # Sort descending by hybrid_score, secondary by semantic_similarity
        results.sort(key=lambda x: (x["hybrid_score"], x["semantic_similarity"]), reverse=True)

        return results[:top_k]


def ingest_events_to_pgvector(
    events: list[dict],
    provider: EmbeddingProvider,
    db_client: Optional[PgVectorDatabaseClient] = None,
    batch_size: int = 50,
) -> int:
    """
    Generic data ingestion path:
    event -> document_builder -> embedding provider -> PostgreSQL historical_event_embeddings

    Args:
        events (list[dict]): Raw historical drilling event dicts.
        provider (EmbeddingProvider): Embedding provider for generating document vectors.
        db_client (PgVectorDatabaseClient, optional): Database client instance.
        batch_size (int): Batch size for vector embedding generation.

    Returns:
        int: Total number of documents successfully embedded and ingested.
    """
    if not events:
        return 0

    client = db_client or PgVectorDatabaseClient()
    documents = events_to_documents(events)
    embedded_docs = embed_documents(documents, provider)

    ingested_count = 0
    for idx, doc in enumerate(embedded_docs):
        meta = doc.get("metadata", {})
        event_id = meta.get("event_id") or meta.get("report_id") or (idx + 1)
        try:
            event_id_int = int(str(event_id).replace("RPT-", "").replace("EVT-", "").replace("W-", ""))
        except ValueError:
            event_id_int = idx + 1

        client.insert_event_embedding(
            event_id=event_id_int,
            content=doc.get("text", ""),
            embedding=doc.get("embedding", []),
            well_id=meta.get("well_id"),
            depth_m=meta.get("depth_m"),
            formation=meta.get("formation"),
            event_type=meta.get("event_type"),
            report_id=str(meta.get("report_id", "")),
            document_type=meta.get("document_type", "historical_event"),
        )
        ingested_count += 1

    return ingested_count
