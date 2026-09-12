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

from src.rag.embeddings import EmbeddingProvider, embed_documents


class FakeEmbeddingProvider(EmbeddingProvider):
    """
    Mock embedding provider for unit tests.
    Does not make any network or external API calls.
    """

    def __init__(self, vector=None):
        self.vector = vector if vector is not None else [0.1, 0.2, 0.3]
        self.call_count = 0
        self.recorded_texts = []

    def embed_text(self, text: str) -> list[float]:
        self.call_count += 1
        self.recorded_texts.append(text)
        return list(self.vector)


def test_embed_text_called():
    """Verify embed_text is invoked and produces expected vector."""
    provider = FakeEmbeddingProvider(vector=[0.1, 0.2, 0.3])
    result = provider.embed_text("test sentence")

    assert provider.call_count == 1, f"Expected 1 call, got {provider.call_count}"
    assert provider.recorded_texts == ["test sentence"]
    assert result == [0.1, 0.2, 0.3]
    print("[PASSED] test_embed_text_called")


def test_embed_documents_adds_embedding_and_preserves_data():
    """
    Verify that embed_documents adds 'embedding' field, preserves original text,
    and preserves metadata.
    """
    provider = FakeEmbeddingProvider(vector=[0.01, -0.02, 0.85])
    document = {
        "text": (
            "Well: TEST-001\n"
            "Depth: 2800 m\n"
            "Formation: Formation X\n"
            "Event: Stuck Pipe\n"
            "Cause: Differential sticking\n"
            "Mitigation: Worked pipe\n"
            "Outcome: Pipe freed"
        ),
        "metadata": {
            "well_id": "TEST-001",
            "depth_m": 2800,
            "formation": "Formation X",
            "event_type": "Stuck Pipe",
            "report_id": "RPT-001",
        },
    }

    result = embed_documents([document], provider)

    # 1. embed_text was called
    assert provider.call_count == 1, f"Expected 1 call, got {provider.call_count}"
    assert provider.recorded_texts[0] == document["text"]

    # 2. Result has 1 document and has 'embedding' field
    assert len(result) == 1, f"Expected 1 document, got {len(result)}"
    assert "embedding" in result[0], "Expected 'embedding' field in output document"
    assert result[0]["embedding"] == [0.01, -0.02, 0.85]

    # 3. Original text is preserved
    assert result[0]["text"] == document["text"], "Original text was not preserved"

    # 4. Metadata is preserved
    assert result[0]["metadata"] == document["metadata"], "Metadata was not preserved"
    assert result[0]["metadata"]["well_id"] == "TEST-001"
    assert result[0]["metadata"]["report_id"] == "RPT-001"
    print("[PASSED] test_embed_documents_adds_embedding_and_preserves_data")


def test_multiple_documents():
    """Verify multiple documents are handled correctly in order."""
    provider = FakeEmbeddingProvider(vector=[0.5, 0.5])
    documents = [
        {"text": f"Document text {i}", "metadata": {"index": i, "well_id": f"WELL_{i}"}}
        for i in range(3)
    ]

    result = embed_documents(documents, provider)

    assert len(result) == 3, f"Expected 3 documents, got {len(result)}"
    assert provider.call_count == 3, f"Expected 3 calls to embed_text, got {provider.call_count}"

    for i, doc in enumerate(result):
        assert doc["text"] == f"Document text {i}"
        assert doc["metadata"]["index"] == i
        assert doc["metadata"]["well_id"] == f"WELL_{i}"
        assert doc["embedding"] == [0.5, 0.5]

    print("[PASSED] test_multiple_documents")


def test_empty_input():
    """Verify empty list and None input return an empty list without crashing."""
    provider = FakeEmbeddingProvider()

    assert embed_documents([], provider) == [], "Expected empty list for [] input"
    assert embed_documents(None, provider) == [], "Expected empty list for None input"
    assert provider.call_count == 0, "Provider should not be called on empty input"
    print("[PASSED] test_empty_input")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest(unittest.FunctionTestCase(test_embed_text_called))
    suite.addTest(unittest.FunctionTestCase(test_embed_documents_adds_embedding_and_preserves_data))
    suite.addTest(unittest.FunctionTestCase(test_multiple_documents))
    suite.addTest(unittest.FunctionTestCase(test_empty_input))
    return suite


def main():
    print("=" * 50)
    print("RUNNING EMBEDDINGS UNIT TESTS")
    print("=" * 50)
    test_embed_text_called()
    test_embed_documents_adds_embedding_and_preserves_data()
    test_multiple_documents()
    test_empty_input()
    print("=" * 50)
    print("ALL EMBEDDINGS UNIT TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
