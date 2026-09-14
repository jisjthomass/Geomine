"""
Hybrid retrieval module for NWIS RAG pipeline.
Combines structured historical filtering (formation, depth tolerance,
event type, nearby wells) with semantic vector retrieval (Gemini embeddings
and cosine similarity).
"""

from typing import Any, Optional
import numpy as np

from .base_retriever import BaseRetriever
from .embeddings import EmbeddingProvider
from .semantic_search import InMemorySemanticIndex, cosine_similarity

# Constants for hybrid ranking weights
SEMANTIC_WEIGHT = 0.60
STRUCTURED_WEIGHT = 0.40

# Structured sub-component weights (sum to 1.0)
WEIGHT_FORMATION = 0.35
WEIGHT_DEPTH = 0.35
WEIGHT_EVENT_TYPE = 0.15
WEIGHT_NEARBY_WELL = 0.15


def matches_dynamic_constraints(
    item: dict,
    formation: Optional[str] = None,
    current_depth: Optional[float] = None,
    depth_tolerance: float = 100.0,
    event_type: Optional[str] = None,
    nearby_well_ids: Optional[list[str]] = None,
) -> bool:
    """
    Evaluates whether a record dictionary satisfies ALL explicitly provided structured constraints.
    Treats every explicitly present constraint as a HARD eligibility filter:
    - event_type: when present, record's event_type must match (case-insensitive)
    - formation: when present, record's formation must match (case-insensitive, allows 'all')
    - depth: when present, record's depth_m must be within [current_depth - depth_tolerance, current_depth + depth_tolerance]
    - nearby_well_ids: when supplied as a non-empty list, record's well_id must be in nearby_well_ids
    Completely dynamic: never hardcodes any event, formation, depth, or well name.
    """
    meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else item
    if not isinstance(meta, dict):
        return False

    # 1. Hard filter: event_type (case-insensitive)
    if event_type is not None and bool(str(event_type).strip()):
        target_event = str(event_type).strip().lower()
        doc_event = str(meta.get("event_type") or "").strip().lower()
        if doc_event != target_event:
            return False

    # 2. Hard filter: formation (case-insensitive)
    if formation is not None and bool(str(formation).strip()):
        target_form = str(formation).strip().lower()
        if target_form != "all":
            doc_form = str(meta.get("formation") or "").strip().lower()
            if doc_form != target_form:
                return False

    # 3. Hard filter: depth within tolerance
    if current_depth is not None:
        doc_depth = meta.get("depth_m")
        if doc_depth is None:
            return False
        try:
            d_val = float(doc_depth)
            target_val = float(current_depth)
            tol = float(depth_tolerance) if depth_tolerance is not None else 100.0
            if abs(d_val - target_val) > tol:
                return False
        except (ValueError, TypeError):
            return False

    # 4. Hard filter: nearby_well_ids (when supplied as a non-empty list)
    if nearby_well_ids is not None and len(nearby_well_ids) > 0:
        doc_well = meta.get("well_id")
        if doc_well is None:
            return False
        nearby_set = {str(w).strip().lower() for w in nearby_well_ids}
        if str(doc_well).strip().lower() not in nearby_set:
            return False

    return True


def filter_candidates(
    items: list[dict],
    formation: Optional[str] = None,
    current_depth: Optional[float] = None,
    depth_tolerance: float = 100.0,
    event_type: Optional[str] = None,
    nearby_well_ids: Optional[list[str]] = None,
) -> list[dict]:
    """
    Filters a list of document or candidate dictionaries strictly by all supplied structured constraints.
    Returns only items satisfying ALL explicit constraints.
    If no constraints are provided, returns items unchanged.
    """
    has_any_constraint = (
        (event_type is not None and bool(str(event_type).strip()))
        or (formation is not None and bool(str(formation).strip()))
        or (current_depth is not None)
        or (nearby_well_ids is not None and len(nearby_well_ids) > 0)
    )
    if not has_any_constraint:
        return list(items)

    return [
        item for item in items
        if matches_dynamic_constraints(
            item=item,
            formation=formation,
            current_depth=current_depth,
            depth_tolerance=depth_tolerance,
            event_type=event_type,
            nearby_well_ids=nearby_well_ids,
        )
    ]



def compute_structured_score(
    metadata: dict,
    formation: Optional[str] = None,
    current_depth: Optional[float] = None,
    depth_tolerance: float = 100.0,
    event_type: Optional[str] = None,
    nearby_well_ids: Optional[list[str]] = None,
) -> float:
    """
    Computes a normalized structured score in [0.0, 1.0] for a document metadata dictionary:
    - Formation match: +0.35
    - Depth within tolerance: +0.35
    - Event type match: +0.15
    - Nearby well match: +0.15

    Args:
        metadata (dict): Event metadata.
        formation (str, optional): Target geological formation name.
        current_depth (float, optional): Target drilling depth in meters.
        depth_tolerance (float): Depth window (+/-) in meters.
        event_type (str, optional): Target event type string.
        nearby_well_ids (list[str], optional): List of relevant/nearby well IDs.

    Returns:
        float: Normalized structured score between 0.0 and 1.0.
    """
    if not isinstance(metadata, dict):
        return 0.0

    score = 0.0

    # 1. Formation matching (case-insensitive) (+0.35)
    if formation is not None and formation.strip():
        doc_formation = str(metadata.get("formation", "")).strip().lower()
        if doc_formation == formation.strip().lower():
            score += WEIGHT_FORMATION

    # 2. Depth within tolerance (+0.35)
    if current_depth is not None:
        doc_depth = metadata.get("depth_m")
        if doc_depth is not None:
            try:
                depth_val = float(doc_depth)
                target_val = float(current_depth)
                tol_val = float(depth_tolerance)
                if abs(depth_val - target_val) <= tol_val:
                    score += WEIGHT_DEPTH
            except (ValueError, TypeError):
                pass

    # 3. Event type matching (case-insensitive) (+0.15)
    if event_type is not None and event_type.strip():
        doc_event = str(metadata.get("event_type", "")).strip().lower()
        if doc_event == event_type.strip().lower():
            score += WEIGHT_EVENT_TYPE

    # 4. Nearby well matching (case-insensitive) (+0.15)
    if nearby_well_ids is not None:
        doc_well = metadata.get("well_id")
        if doc_well is not None:
            nearby_set = {str(w).strip().lower() for w in nearby_well_ids}
            if str(doc_well).strip().lower() in nearby_set:
                score += WEIGHT_NEARBY_WELL

    return float(np.clip(score, 0.0, 1.0))


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever combining structured domain filtering with vector semantic retrieval.
    Decoupled from specific embedding providers, database engines, and LLMs.
    """

    def __init__(
        self,
        documents: Optional[list[dict]] = None,
        index: Optional[InMemorySemanticIndex] = None,
    ):
        """
        Initialize with a list of historical document dicts and/or an InMemorySemanticIndex.

        Args:
            documents (list[dict], optional): List of document dicts with 'text', 'metadata', 'embedding'.
            index (InMemorySemanticIndex, optional): Pre-built semantic index.
        """
        self.index = index
        if documents:
            self.documents = list(documents)
        elif index and hasattr(index, "_documents"):
            self.documents = list(index._documents)
        else:
            self.documents = []

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
        Execute hybrid retrieval across indexed documents.

        1. Computes structured scores for documents.
        2. Filters matching candidates (falls back to broader document set if 0 matches).
        3. Computes semantic similarity for candidates via provider.embed_text(query).
        4. Normalizes semantic similarity: (sim + 1) / 2.
        5. Computes hybrid_score = 0.6 * semantic_norm + 0.4 * structured_score.
        6. Sorts descending by hybrid_score and returns top_k results.

        Returns:
            list[dict]: Ranked documents containing 'text', 'metadata', 'embedding',
                        'semantic_similarity', 'structured_score', and 'hybrid_score'.
        """
        if not self.documents or top_k <= 0:
            return []

        if provider is None or not hasattr(provider, "embed_text"):
            raise ValueError("A valid EmbeddingProvider instance is required for hybrid retrieval.")

        # Check if any structured constraints are active
        has_structured_constraints = (
            (formation is not None and bool(str(formation).strip()))
            or (current_depth is not None)
            or (event_type is not None and bool(str(event_type).strip()))
            or (nearby_well_ids is not None and len(nearby_well_ids) > 0)
        )

        # 1. HARD FILTER BY ALL EXPLICIT STRUCTURED CONSTRAINTS
        # When explicit structured constraints are present (formation, depth, event_type, nearby_wells),
        # only records that satisfy ALL explicit constraints remain eligible for retrieval.
        # Semantic similarity ranking happens ONLY after this hard structured filtering.
        # Semantic similarity must NEVER re-introduce a record that failed a hard structured constraint.
        if has_structured_constraints:
            eligible_documents = filter_candidates(
                items=self.documents,
                formation=formation,
                current_depth=current_depth,
                depth_tolerance=depth_tolerance,
                event_type=event_type,
                nearby_well_ids=nearby_well_ids,
            )
            # If explicit constraints exist and zero records satisfy them, return zero results
            if not eligible_documents:
                return []
        else:
            # Genuinely broad/general query without structured constraints
            eligible_documents = self.documents

        # Pre-calculate structured scores for all eligible documents
        doc_structured_scores = []
        for doc in eligible_documents:
            meta = doc.get("metadata", {})
            s_score = compute_structured_score(
                metadata=meta,
                formation=formation,
                current_depth=current_depth,
                depth_tolerance=depth_tolerance,
                event_type=event_type,
                nearby_well_ids=nearby_well_ids,
            )
            doc_structured_scores.append((doc, s_score))

        candidates = doc_structured_scores

        # Generate query embedding
        query_embedding = provider.embed_text(query)
        if not query_embedding:
            return []

        results = []
        for doc, s_score in candidates:
            doc_embedding = doc.get("embedding")
            if not doc_embedding:
                continue

            # Semantic similarity
            cos_sim = cosine_similarity(query_embedding, doc_embedding)
            # Normalize cosine similarity [-1, 1] to [0, 1]
            semantic_norm = float(np.clip((cos_sim + 1.0) / 2.0, 0.0, 1.0))

            # Hybrid score
            hybrid_score = float(SEMANTIC_WEIGHT * semantic_norm + STRUCTURED_WEIGHT * s_score)

            # Build result without mutating original doc
            res = {
                "text": doc.get("text", ""),
                "metadata": dict(doc.get("metadata", {})),
                "embedding": list(doc_embedding),
                "semantic_similarity": float(cos_sim),
                "structured_score": float(s_score),
                "hybrid_score": hybrid_score,
            }
            results.append(res)

        # Sort by hybrid_score descending (secondary by semantic_similarity)
        results.sort(key=lambda x: (x["hybrid_score"], x["semantic_similarity"]), reverse=True)

        return results[:top_k]
 
 
# Alias for architectural clarity in multi-backend RAG systems
InMemoryRetriever = HybridRetriever
