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
from src.rag.retrieval_service import RAGRetrievalService


class MockTrackingEmbeddingProvider(EmbeddingProvider):
    """
    Mock embedding provider that counts invocations to verify
    caching / preparation behavior without re-embedding.
    """

    def __init__(self, vector=None):
        self.vector = vector or [1.0, 0.0, 0.0]
        self.call_count = 0
        self.recorded_calls = []

    def embed_text(self, text: str) -> list[float]:
        self.call_count += 1
        self.recorded_calls.append(text)
        return list(self.vector)


def sample_events():
    return [
        {
            "well_id": "WELL_001",
            "depth_m": 2800,
            "formation": "Formation X",
            "event_type": "Stuck Pipe",
            "cause": "Differential sticking",
            "mitigation": "Worked pipe",
            "outcome": "Pipe freed",
            "report_id": "RPT_001",
        },
        {
            "well_id": "WELL_002",
            "depth_m": 4100,
            "formation": "Formation B",
            "event_type": "Torque Spike",
            "cause": "Formation interaction",
            "mitigation": "Reduced WOB",
            "outcome": "Torque stabilized",
            "report_id": "RPT_002",
        },
    ]


def test_service_prepare_documents():
    """Test 1: Service can prepare documents and marks itself prepared."""
    provider = MockTrackingEmbeddingProvider()
    service = RAGRetrievalService(events=sample_events(), provider=provider)

    assert not service.is_prepared
    service.prepare()
    assert service.is_prepared
    assert len(service._documents) == 2
    assert len(service._embedded_documents) == 2
    print("[PASSED] test_service_prepare_documents")


def test_service_builds_index():
    """Test 2: Service builds in-memory semantic index with embedded documents."""
    provider = MockTrackingEmbeddingProvider()
    service = RAGRetrievalService(events=sample_events(), provider=provider, auto_prepare=True)

    assert service._index is not None
    assert len(service._index) == 2
    print("[PASSED] test_service_builds_index")


def test_retrieval_returns_ranked_evidence():
    """Test 3: Retrieval returns ranked evidence with all required score fields."""
    provider = MockTrackingEmbeddingProvider()
    service = RAGRetrievalService(events=sample_events(), provider=provider, auto_prepare=True)

    results = service.retrieve(query="stuck pipe problems", top_k=2)

    assert len(results) == 2
    for r in results:
        assert "text" in r
        assert "metadata" in r
        assert "embedding" in r
        assert "semantic_similarity" in r
        assert "structured_score" in r
        assert "hybrid_score" in r
    print("[PASSED] test_retrieval_returns_ranked_evidence")


def test_structured_query_parameters_passed():
    """Test 4: Structured query parameters are passed to retriever and affect scoring."""
    provider = MockTrackingEmbeddingProvider()
    service = RAGRetrievalService(events=sample_events(), provider=provider, auto_prepare=True)

    results = service.retrieve(
        query="stuck pipe problems",
        current_depth=2800,
        formation="Formation X",
        depth_tolerance=50,
        event_type="Stuck Pipe",
        nearby_well_ids=["WELL_001"],
        top_k=2,
    )

    top = results[0]
    assert top["metadata"]["well_id"] == "WELL_001"
    # Matches formation (+0.35), depth (+0.35), event (+0.15), well (+0.15) = 1.0
    assert top["structured_score"] == 1.0
    assert top["hybrid_score"] > 0.8
    print("[PASSED] test_structured_query_parameters_passed")


def test_metadata_preserved():
    """Test 5: Original event metadata fields are strictly preserved in retrieval results."""
    provider = MockTrackingEmbeddingProvider()
    service = RAGRetrievalService(events=sample_events(), provider=provider, auto_prepare=True)

    results = service.retrieve(query="anything", top_k=2)
    meta_keys = {"well_id", "depth_m", "formation", "event_type", "report_id"}

    for r in results:
        assert meta_keys.issubset(set(r["metadata"].keys()))
    print("[PASSED] test_metadata_preserved")


def test_no_reembedding_on_repeated_retrieval():
    """Test 6: Documents are embedded only once during prepare(); no re-embedding on subsequent searches."""
    provider = MockTrackingEmbeddingProvider()
    service = RAGRetrievalService(events=sample_events(), provider=provider)

    # Prepare embeds the 2 documents
    service.prepare()
    embed_count_after_prep = provider.call_count
    assert embed_count_after_prep == 2

    # Second prepare call must be a no-op
    service.prepare()
    assert provider.call_count == embed_count_after_prep

    # Execute 3 separate retrieve calls
    service.retrieve("query 1")
    service.retrieve("query 2")
    service.retrieve("query 3")

    # Each retrieve call only embeds the query string (3 query embeddings total)
    assert provider.call_count == embed_count_after_prep + 3
    # Verify the last 3 calls were for the queries, not document texts
    assert provider.recorded_calls[-3:] == ["query 1", "query 2", "query 3"]
    print("[PASSED] test_no_reembedding_on_repeated_retrieval")


def test_empty_dataset_behavior():
    """Test 7: Empty dataset behaves safely without crashing."""
    provider = MockTrackingEmbeddingProvider()
    service = RAGRetrievalService(events=[], provider=provider)

    service.prepare()
    assert service.is_prepared
    assert len(service._documents) == 0

    results = service.retrieve(query="search", current_depth=2000, formation="F", top_k=5)
    assert results == []
    print("[PASSED] test_empty_dataset_behavior")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest(unittest.FunctionTestCase(test_service_prepare_documents))
    suite.addTest(unittest.FunctionTestCase(test_service_builds_index))
    suite.addTest(unittest.FunctionTestCase(test_retrieval_returns_ranked_evidence))
    suite.addTest(unittest.FunctionTestCase(test_structured_query_parameters_passed))
    suite.addTest(unittest.FunctionTestCase(test_metadata_preserved))
    suite.addTest(unittest.FunctionTestCase(test_no_reembedding_on_repeated_retrieval))
    suite.addTest(unittest.FunctionTestCase(test_empty_dataset_behavior))
    return suite


def main():
    print("=" * 50)
    print("RUNNING RAG RETRIEVAL SERVICE UNIT TESTS")
    print("=" * 50)
    test_service_prepare_documents()
    test_service_builds_index()
    test_retrieval_returns_ranked_evidence()
    test_structured_query_parameters_passed()
    test_metadata_preserved()
    test_no_reembedding_on_repeated_retrieval()
    test_empty_dataset_behavior()
    print("=" * 50)
    print("ALL RAG RETRIEVAL SERVICE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
