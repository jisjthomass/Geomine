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
from src.rag.hybrid_retrieval import (
    HybridRetriever,
    SEMANTIC_WEIGHT,
    STRUCTURED_WEIGHT,
    WEIGHT_FORMATION,
    WEIGHT_DEPTH,
    WEIGHT_EVENT_TYPE,
    WEIGHT_NEARBY_WELL,
    compute_structured_score,
)


class DeterministicFakeEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic mock embedding provider for testing hybrid retrieval.
    Does not make any network or external API calls.
    """

    def __init__(self, mapping=None, default_vector=None):
        self.mapping = mapping or {}
        self.default_vector = default_vector or [1.0, 0.0, 0.0]

    def embed_text(self, text: str) -> list[float]:
        if text in self.mapping:
            return list(self.mapping[text])
        return list(self.default_vector)


def build_synthetic_dataset():
    """
    Builds the required synthetic dataset covering:
    1. same formation + close depth + matching event
    2. same formation + far depth
    3. different formation + close depth
    4. nearby well
    5. non-nearby well
    6. semantically similar but structurally less relevant event
    """
    docs = [
        # 1. same formation + close depth + matching event
        {
            "text": "Well: WELL_NEAR\nDepth: 2800 m\nFormation: Formation X\nEvent: Stuck Pipe",
            "metadata": {
                "well_id": "WELL_NEAR",
                "depth_m": 2800,
                "formation": "Formation X",
                "event_type": "Stuck Pipe",
            },
            # vector giving cosine similarity 0.8 with query [1.0, 0.0, 0.0]
            "embedding": [0.8, 0.6, 0.0],
        },
        # 2. same formation + far depth
        {
            "text": "Well: WELL_FAR1\nDepth: 4500 m\nFormation: Formation X\nEvent: Stuck Pipe",
            "metadata": {
                "well_id": "WELL_FAR1",
                "depth_m": 4500,
                "formation": "Formation X",
                "event_type": "Stuck Pipe",
            },
            "embedding": [0.8, 0.6, 0.0],
        },
        # 3. different formation + close depth
        {
            "text": "Well: WELL_FAR2\nDepth: 2810 m\nFormation: Formation Y\nEvent: Stuck Pipe",
            "metadata": {
                "well_id": "WELL_FAR2",
                "depth_m": 2810,
                "formation": "Formation Y",
                "event_type": "Stuck Pipe",
            },
            "embedding": [0.8, 0.6, 0.0],
        },
        # 4. nearby well
        {
            "text": "Well: WELL_NEAR\nDepth: 1200 m\nFormation: Formation Z\nEvent: Mud Loss",
            "metadata": {
                "well_id": "WELL_NEAR",
                "depth_m": 1200,
                "formation": "Formation Z",
                "event_type": "Mud Loss",
            },
            "embedding": [0.0, 1.0, 0.0],
        },
        # 5. non-nearby well
        {
            "text": "Well: WELL_FAR3\nDepth: 1200 m\nFormation: Formation Z\nEvent: Mud Loss",
            "metadata": {
                "well_id": "WELL_FAR3",
                "depth_m": 1200,
                "formation": "Formation Z",
                "event_type": "Mud Loss",
            },
            "embedding": [0.0, 1.0, 0.0],
        },
        # 6. semantically similar but structurally less relevant event
        {
            "text": "Well: WELL_FAR4\nDepth: 4500 m\nFormation: Formation Y\nEvent: Stuck Pipe",
            "metadata": {
                "well_id": "WELL_FAR4",
                "depth_m": 4500,
                "formation": "Formation Y",
                "event_type": "Stuck Pipe",
            },
            # vector giving perfect cosine similarity 1.0 with query [1.0, 0.0, 0.0]
            "embedding": [1.0, 0.0, 0.0],
        },
    ]
    return docs


def test_formation_matching():
    """Test A: Formation match awards +0.35 to structured score."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider()

    # Query with formation="Formation X"
    results = retriever.retrieve(
        query="test query",
        provider=provider,
        formation="Formation X",
        top_k=10,
    )

    formation_x_results = [r for r in results if r["metadata"]["formation"] == "Formation X"]
    for r in formation_x_results:
        assert r["structured_score"] >= WEIGHT_FORMATION
    print("[PASSED] test_formation_matching")


def test_depth_tolerance():
    """Test B: Events within depth tolerance receive +0.35 depth score."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider()

    # Query at 2800m with 50m tolerance
    results = retriever.retrieve(
        query="test query",
        provider=provider,
        current_depth=2800,
        depth_tolerance=50,
        top_k=10,
    )

    for r in results:
        depth = r["metadata"]["depth_m"]
        if abs(depth - 2800) <= 50:
            assert r["structured_score"] >= WEIGHT_DEPTH
    print("[PASSED] test_depth_tolerance")


def test_event_type_matching():
    """Test C: Matching event_type awards +0.15."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider()

    results = retriever.retrieve(
        query="test query",
        provider=provider,
        event_type="Stuck Pipe",
        top_k=10,
    )

    stuck_pipe_results = [r for r in results if r["metadata"]["event_type"] == "Stuck Pipe"]
    for r in stuck_pipe_results:
        assert r["structured_score"] >= WEIGHT_EVENT_TYPE
    print("[PASSED] test_event_type_matching")


def test_nearby_well_preference():
    """Test D: Nearby well match awards +0.15 preference over non-nearby wells."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider()

    results = retriever.retrieve(
        query="test query",
        provider=provider,
        nearby_well_ids=["WELL_NEAR"],
        top_k=10,
    )

    near_results = [r for r in results if r["metadata"]["well_id"] == "WELL_NEAR"]
    for r in near_results:
        assert r["structured_score"] >= WEIGHT_NEARBY_WELL
    print("[PASSED] test_nearby_well_preference")


def test_semantic_ranking():
    """Test E: Semantic ranking determines order when structured score is identical."""
    doc_high_semantic = {
        "text": "High semantic event",
        "metadata": {"well_id": "W1", "formation": "F1", "depth_m": 2000},
        "embedding": [1.0, 0.0, 0.0],
    }
    doc_low_semantic = {
        "text": "Low semantic event",
        "metadata": {"well_id": "W2", "formation": "F1", "depth_m": 2000},
        "embedding": [0.5, 0.866, 0.0],
    }

    retriever = HybridRetriever(documents=[doc_low_semantic, doc_high_semantic])
    provider = DeterministicFakeEmbeddingProvider(default_vector=[1.0, 0.0, 0.0])

    results = retriever.retrieve(query="search", provider=provider, formation="F1", top_k=2)

    assert results[0]["text"] == "High semantic event"
    assert results[0]["semantic_similarity"] > results[1]["semantic_similarity"]
    print("[PASSED] test_semantic_ranking")


def test_hybrid_score_calculation():
    """Test F: Hybrid score accurately matches the 0.6 * semantic_norm + 0.4 * structured formula."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    # Query vector is [1.0, 0.0, 0.0]
    provider = DeterministicFakeEmbeddingProvider(default_vector=[1.0, 0.0, 0.0])

    results = retriever.retrieve(
        query="test query",
        provider=provider,
        current_depth=2800,
        formation="Formation X",
        depth_tolerance=100,
        event_type="Stuck Pipe",
        nearby_well_ids=["WELL_NEAR"],
        top_k=1,
    )

    top_doc = results[0]
    # Doc 1: matches all 4 structured filters -> structured_score = 1.0
    # Embedding [0.8, 0.6, 0.0] -> cos_sim = 0.8
    # semantic_norm = (0.8 + 1) / 2 = 0.9
    # hybrid_score = 0.6 * 0.9 + 0.4 * 1.0 = 0.54 + 0.40 = 0.94
    expected_structured = 1.0
    expected_semantic = 0.8
    expected_semantic_norm = (0.8 + 1.0) / 2.0
    expected_hybrid = (SEMANTIC_WEIGHT * expected_semantic_norm) + (STRUCTURED_WEIGHT * expected_structured)

    assert math.isclose(top_doc["structured_score"], expected_structured, rel_tol=1e-4)
    assert math.isclose(top_doc["semantic_similarity"], expected_semantic, rel_tol=1e-4)
    assert math.isclose(top_doc["hybrid_score"], expected_hybrid, rel_tol=1e-4)
    print("[PASSED] test_hybrid_score_calculation")


def test_results_sorted_by_hybrid_score():
    """Test G: Results are strictly sorted descending by hybrid_score."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider(default_vector=[1.0, 0.0, 0.0])

    results = retriever.retrieve(
        query="test query",
        provider=provider,
        current_depth=2800,
        formation="Formation X",
        depth_tolerance=100,
        top_k=10,
    )

    for i in range(len(results) - 1):
        assert results[i]["hybrid_score"] >= results[i + 1]["hybrid_score"], (
            f"Results not sorted: {results[i]['hybrid_score']} < {results[i+1]['hybrid_score']}"
        )
    print("[PASSED] test_results_sorted_by_hybrid_score")


def test_top_k():
    """Test H: top_k parameter limits output appropriately."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider()

    for k in [1, 2, 3]:
        results = retriever.retrieve(query="test", provider=provider, top_k=k)
        assert len(results) == k, f"Expected {k} results, got {len(results)}"
    print("[PASSED] test_top_k")


def test_structured_filtering_no_candidates_fallback():
    """Test I: When structured filtering produces 0 candidates, falls back to broader document set."""
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider()

    # Query with non-existent formation and impossible depth
    results = retriever.retrieve(
        query="test",
        provider=provider,
        formation="NonExistentFormation999",
        current_depth=99999,
        top_k=3,
    )

    # Should not return empty list; falls back to broader document set
    assert len(results) == 3, f"Expected 3 fallback results, got {len(results)}"
    for r in results:
        # Structured score is 0.0 since none matched
        assert r["structured_score"] == 0.0
        # Hybrid score is driven by semantic similarity
        assert r["hybrid_score"] > 0.0
    print("[PASSED] test_structured_filtering_no_candidates_fallback")


def test_correct_formation_depth_outranks_higher_semantic_similarity():
    """
    CRITICAL TEST:
    Proves that a semantically relevant event from the correct formation/depth
    can outrank a semantically more similar event from the wrong formation/depth.
    """
    docs = build_synthetic_dataset()
    retriever = HybridRetriever(documents=docs)
    provider = DeterministicFakeEmbeddingProvider(default_vector=[1.0, 0.0, 0.0])

    # Query targeting Formation X at 2800m
    results = retriever.retrieve(
        query="stuck pipe in borehole",
        provider=provider,
        current_depth=2800,
        formation="Formation X",
        depth_tolerance=100,
        event_type="Stuck Pipe",
        top_k=5,
    )

    # In our synthetic dataset:
    # Doc 1: Formation X, 2800m, Stuck Pipe (cos_sim = 0.8, structured_score = 1.0 -> hybrid = 0.94)
    # Doc 6: Formation Y, 4500m, Stuck Pipe (cos_sim = 1.0 [higher!], structured_score = 0.15 -> hybrid = 0.66)
    rank_1 = results[0]
    assert rank_1["metadata"]["formation"] == "Formation X"
    assert rank_1["metadata"]["depth_m"] == 2800
    assert rank_1["metadata"]["well_id"] == "WELL_NEAR"

    # Verify Doc 1 outranks Doc 6
    doc6_results = [r for r in results if r["metadata"]["well_id"] == "WELL_FAR4"]
    assert len(doc6_results) == 1
    doc_6 = doc6_results[0]

    # Doc 6 had higher semantic similarity
    assert doc_6["semantic_similarity"] > rank_1["semantic_similarity"], "Doc 6 should have higher semantic similarity"
    # But Doc 1 had higher hybrid score and outranked it!
    assert rank_1["hybrid_score"] > doc_6["hybrid_score"], "Doc 1 should outrank Doc 6 in hybrid score"
    print("[PASSED] test_correct_formation_depth_outranks_higher_semantic_similarity")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest(unittest.FunctionTestCase(test_formation_matching))
    suite.addTest(unittest.FunctionTestCase(test_depth_tolerance))
    suite.addTest(unittest.FunctionTestCase(test_event_type_matching))
    suite.addTest(unittest.FunctionTestCase(test_nearby_well_preference))
    suite.addTest(unittest.FunctionTestCase(test_semantic_ranking))
    suite.addTest(unittest.FunctionTestCase(test_hybrid_score_calculation))
    suite.addTest(unittest.FunctionTestCase(test_results_sorted_by_hybrid_score))
    suite.addTest(unittest.FunctionTestCase(test_top_k))
    suite.addTest(unittest.FunctionTestCase(test_structured_filtering_no_candidates_fallback))
    suite.addTest(unittest.FunctionTestCase(test_correct_formation_depth_outranks_higher_semantic_similarity))
    return suite


def main():
    print("=" * 50)
    print("RUNNING HYBRID RETRIEVAL UNIT TESTS")
    print("=" * 50)
    test_formation_matching()
    test_depth_tolerance()
    test_event_type_matching()
    test_nearby_well_preference()
    test_semantic_ranking()
    test_hybrid_score_calculation()
    test_results_sorted_by_hybrid_score()
    test_top_k()
    test_structured_filtering_no_candidates_fallback()
    test_correct_formation_depth_outranks_higher_semantic_similarity()
    print("=" * 50)
    print("ALL HYBRID RETRIEVAL UNIT TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
