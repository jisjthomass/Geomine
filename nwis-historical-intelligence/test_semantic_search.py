import math
import os
import sys
import unittest

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.rag.embeddings import EmbeddingProvider
from src.rag.semantic_search import InMemorySemanticIndex, cosine_similarity


class DeterministicFakeEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic mock embedding provider for unit tests.
    Does not call external APIs.
    """

    def __init__(self, mapping=None, default_vector=None):
        self.mapping = mapping or {}
        self.default_vector = default_vector or [0.0, 0.0, 1.0]
        self.call_count = 0

    def embed_text(self, text: str) -> list[float]:
        self.call_count += 1
        if text in self.mapping:
            return list(self.mapping[text])
        return list(self.default_vector)


def test_cosine_similarity_identical():
    """Identical non-zero vectors should return approx 1.0."""
    v1 = [1.0, 2.0, 3.0]
    v2 = [1.0, 2.0, 3.0]
    sim = cosine_similarity(v1, v2)
    assert math.isclose(sim, 1.0, rel_tol=1e-5), f"Expected 1.0, got {sim}"
    print("[PASSED] test_cosine_similarity_identical")


def test_cosine_similarity_orthogonal():
    """Orthogonal vectors should return approx 0.0."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    sim = cosine_similarity(v1, v2)
    assert math.isclose(sim, 0.0, abs_tol=1e-5), f"Expected 0.0, got {sim}"
    print("[PASSED] test_cosine_similarity_orthogonal")


def test_cosine_similarity_zero_vector():
    """Zero vector should return 0.0 safely without crashing or division by zero."""
    v1 = [0.0, 0.0, 0.0]
    v2 = [1.0, 2.0, 3.0]
    sim = cosine_similarity(v1, v2)
    assert sim == 0.0, f"Expected 0.0 for zero vector, got {sim}"

    sim2 = cosine_similarity(v1, v1)
    assert sim2 == 0.0, f"Expected 0.0 for two zero vectors, got {sim2}"
    print("[PASSED] test_cosine_similarity_zero_vector")


def test_cosine_similarity_mismatched_dimensions():
    """Mismatched vector dimensions should raise a ValueError."""
    v1 = [1.0, 2.0]
    v2 = [1.0, 2.0, 3.0]
    try:
        cosine_similarity(v1, v2)
        assert False, "Expected ValueError was not raised for mismatched dimensions"
    except ValueError as e:
        assert "dimensions do not match" in str(e)
    print("[PASSED] test_cosine_similarity_mismatched_dimensions")


def test_indexing_add_len_clear():
    """Verify document addition, length tracking, and clearing."""
    index = InMemorySemanticIndex()
    assert len(index) == 0

    docs = [
        {"text": "Doc 1", "metadata": {"id": 1}, "embedding": [1.0, 0.0]},
        {"text": "Doc 2", "metadata": {"id": 2}, "embedding": [0.0, 1.0]},
    ]
    index.add_documents(docs)
    assert len(index) == 2, f"Expected length 2, got {len(index)}"

    # Adding empty or invalid should not crash
    index.add_documents([])
    index.add_documents([{"text": "No embedding"}])
    assert len(index) == 2

    # Clear should reset index
    index.clear()
    assert len(index) == 0
    print("[PASSED] test_indexing_add_len_clear")


def test_search_ranking_and_top_k():
    """
    Verify search ranks highest similarity first, respects top_k,
    and does not mutate original documents.
    """
    index = InMemorySemanticIndex()

    # Pre-defined orthogonal / angled vectors
    docs = [
        {"text": "Stuck Pipe Event", "metadata": {"event": "Stuck Pipe"}, "embedding": [1.0, 0.0, 0.0]},
        {"text": "Mud Loss Event", "metadata": {"event": "Mud Loss"}, "embedding": [0.0, 1.0, 0.0]},
        {"text": "Partial Sticking Event", "metadata": {"event": "Partial Sticking"}, "embedding": [0.7071, 0.7071, 0.0]},
    ]
    index.add_documents(docs)

    # Provider returns [1.0, 0.0, 0.0] for query
    provider = DeterministicFakeEmbeddingProvider(
        mapping={"stuck pipe query": [1.0, 0.0, 0.0]}
    )

    # Search top 2
    results = index.search(query="stuck pipe query", provider=provider, top_k=2)

    assert len(results) == 2, f"Expected 2 results with top_k=2, got {len(results)}"

    # 1. Correct highest-ranked document
    top_doc = results[0]
    assert top_doc["metadata"]["event"] == "Stuck Pipe"
    assert math.isclose(top_doc["similarity"], 1.0, rel_tol=1e-4)

    # 2. Descending similarity order
    second_doc = results[1]
    assert second_doc["metadata"]["event"] == "Partial Sticking"
    assert top_doc["similarity"] >= second_doc["similarity"]

    # 3. Required fields present
    for r in results:
        assert "text" in r
        assert "metadata" in r
        assert "embedding" in r
        assert "similarity" in r

    # 4. Original documents are not mutated
    assert "similarity" not in docs[0]

    # Search top 5 returns all 3 available
    all_results = index.search(query="stuck pipe query", provider=provider, top_k=5)
    assert len(all_results) == 3
    assert all_results[2]["metadata"]["event"] == "Mud Loss"
    assert math.isclose(all_results[2]["similarity"], 0.0, abs_tol=1e-4)

    print("[PASSED] test_search_ranking_and_top_k")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest(unittest.FunctionTestCase(test_cosine_similarity_identical))
    suite.addTest(unittest.FunctionTestCase(test_cosine_similarity_orthogonal))
    suite.addTest(unittest.FunctionTestCase(test_cosine_similarity_zero_vector))
    suite.addTest(unittest.FunctionTestCase(test_cosine_similarity_mismatched_dimensions))
    suite.addTest(unittest.FunctionTestCase(test_indexing_add_len_clear))
    suite.addTest(unittest.FunctionTestCase(test_search_ranking_and_top_k))
    return suite


def main():
    print("=" * 50)
    print("RUNNING SEMANTIC SEARCH UNIT TESTS")
    print("=" * 50)
    test_cosine_similarity_identical()
    test_cosine_similarity_orthogonal()
    test_cosine_similarity_zero_vector()
    test_cosine_similarity_mismatched_dimensions()
    test_indexing_add_len_clear()
    test_search_ranking_and_top_k()
    print("=" * 50)
    print("ALL SEMANTIC SEARCH UNIT TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
