"""
In-memory semantic search and vector similarity index for NWIS RAG pipeline.
Decoupled from PostgreSQL, PostGIS, GIS distance, query parsing, and Gemini answer generation.
"""

from typing import Optional
import numpy as np

from .embeddings import EmbeddingProvider


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Calculate the cosine similarity between two numeric vectors.

    Args:
        a (list[float]): First vector.
        b (list[float]): Second vector.

    Returns:
        float: Cosine similarity in range [-1.0, 1.0], or 0.0 for zero vectors.

    Raises:
        ValueError: If vector dimensions do not match.
    """
    if len(a) != len(b):
        raise ValueError(
            f"Vector dimensions do not match: len(a)={len(a)}, len(b)={len(b)}"
        )

    vec_a = np.asarray(a, dtype=float)
    vec_b = np.asarray(b, dtype=float)

    norm_a = float(np.linalg.norm(vec_a))
    norm_b = float(np.linalg.norm(vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    similarity = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
    return float(np.clip(similarity, -1.0, 1.0))


class InMemorySemanticIndex:
    """
    In-memory semantic vector index for cosine similarity retrieval.
    Stores pre-embedded documents and performs top-k semantic search.
    """

    def __init__(self):
        self._documents: list[dict] = []

    def add_documents(self, documents: list[dict]) -> None:
        """
        Add documents with pre-computed embeddings to the index.

        Each document should have:
        {
            "text": "...",
            "metadata": {...},
            "embedding": [...]
        }

        Args:
            documents (list[dict]): Documents to index.
        """
        if not documents:
            return

        for doc in documents:
            if not isinstance(doc, dict):
                continue
            if "embedding" not in doc or not doc["embedding"]:
                continue
            # Store a copy to avoid mutating caller references
            self._documents.append(dict(doc))

    def search(
        self,
        query: str,
        provider: EmbeddingProvider,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search indexed documents by cosine similarity against the query embedding.

        Args:
            query (str): Search query string.
            provider (EmbeddingProvider): Provider to generate query embedding.
            top_k (int): Maximum number of results to return.

        Returns:
            list[dict]: Top k matching documents sorted by similarity descending.
                        Each result contains 'text', 'metadata', 'embedding',
                        and 'similarity'.
        """
        if not self._documents or top_k <= 0:
            return []

        if provider is None or not hasattr(provider, "embed_text"):
            raise ValueError("A valid EmbeddingProvider instance is required for search.")

        query_embedding = provider.embed_text(query)
        if not query_embedding:
            return []

        scored_docs = []
        for doc in self._documents:
            doc_embedding = doc.get("embedding")
            if not doc_embedding:
                continue

            sim = cosine_similarity(query_embedding, doc_embedding)
            # Create a copy so original document in index is not mutated
            res = dict(doc)
            res["similarity"] = round(float(sim), 4)
            scored_docs.append(res)

        # Sort highest similarity first
        scored_docs.sort(key=lambda x: x["similarity"], reverse=True)

        return scored_docs[:top_k]

    def clear(self) -> None:
        """Clear all indexed documents."""
        self._documents.clear()

    def __len__(self) -> int:
        """Return the number of currently indexed documents."""
        return len(self._documents)
