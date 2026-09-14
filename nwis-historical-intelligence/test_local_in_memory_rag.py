"""
Local In-Memory RAG Verification Test & Demo (Stage 1-6)

Verifies the complete natural language RAG pipeline locally WITHOUT requiring
PostgreSQL or pgvector:

User Question
    ↓
LLMQueryParser (Gemini)
    ↓
Gemini Embedding Provider (gemini-embedding-001)
    ↓
InMemorySemanticIndex (NumPy cosine similarity)
    ↓
HybridRetriever (Semantic + Domain Structured Scoring)
    ↓
ContextBuilder (Markdown Grounding Format)
    ↓
HistoricalAnswerGenerator (Gemini grounded prompt)
    ↓
Final Grounded Answer (Findings + Inference)

Dataset: Existing synthetic historical drilling events (nwis_mock_historical_events.json)
"""

import json
import os
import sys
import unittest
from typing import Optional

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv() or os.path.join(PROJECT_ROOT, ".env"))

from src.rag.document_builder import events_to_documents
from src.rag.embeddings import EmbeddingProvider, GeminiEmbeddingProvider, embed_documents
from src.rag.semantic_search import InMemorySemanticIndex
from src.rag.hybrid_retrieval import HybridRetriever, compute_structured_score
from src.rag.retrieval_service import RAGRetrievalService
from src.rag.context_builder import build_rag_context
from src.llm.base import LLMProvider
from src.llm.gemini import GeminiProvider
from src.llm.query_parser import LLMQueryParser
from src.llm.answer_generator import HistoricalAnswerGenerator
from src.llm.query_service import HistoricalQueryService


class CachedEmbeddingProvider(EmbeddingProvider):
    """
    Wraps an underlying EmbeddingProvider with an in-memory query cache
    to avoid redundant API requests for identical queries during testing.
    """

    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider
        self.cache: dict[str, list[float]] = {}

    def embed_text(self, text: str) -> list[float]:
        if text in self.cache:
            return self.cache[text]
        vec = self.provider.embed_text(text)
        self.cache[text] = vec
        return vec


def load_local_synthetic_events() -> list[dict]:
    """
    Loads synthetic historical drilling events directly from local JSON dataset.
    Completely independent of PostgreSQL and pgvector.
    """
    dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Synthetic dataset not found at: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        events = json.load(f)
    return events


def load_or_generate_embedded_documents(
    events: list[dict],
    provider: EmbeddingProvider,
) -> list[dict]:
    """
    Prepares documents and attaches embeddings.
    Reuses cached embeddings from nwis_mock_embeddings_cache.json if available
    to prevent redundant Gemini embedding API quota consumption.
    """
    docs = events_to_documents(events)
    cache_path = os.path.join(PROJECT_ROOT, "nwis_mock_embeddings_cache.json")

    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    missing_docs = []
    embedded_docs = []
    for doc in docs:
        text = doc["text"]
        if text in cache:
            doc_copy = dict(doc)
            doc_copy["embedding"] = cache[text]
            embedded_docs.append(doc_copy)
        else:
            missing_docs.append(doc)

    if missing_docs:
        print(f"[Notice] Generating embeddings for {len(missing_docs)} uncached documents...")
        newly_embedded = embed_documents(missing_docs, provider)
        for doc in newly_embedded:
            cache[doc["text"]] = doc["embedding"]
            embedded_docs.append(doc)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception:
            pass

    return embedded_docs


# Shared global resources for demo and tests
_SHARED_RESOURCES = {}

def get_shared_pipeline():
    """Initializes and caches shared pipeline components."""
    if not _SHARED_RESOURCES:
        events = load_local_synthetic_events()
        raw_embedding_provider = GeminiEmbeddingProvider()
        cached_embedding_provider = CachedEmbeddingProvider(raw_embedding_provider)
        llm_provider = GeminiProvider()

        embedded_docs = load_or_generate_embedded_documents(events, cached_embedding_provider)
        rag_service = RAGRetrievalService(
            events=embedded_docs,
            provider=cached_embedding_provider,
            backend="in_memory",
            auto_prepare=True,
        )
        offset_wells = ["WELL_004", "WELL_006", "WELL_008", "WELL_014", "WELL_017", "WELL_021"]
        query_service = HistoricalQueryService(
            provider=llm_provider,
            events=events,
            rag_service=rag_service,
        )
        _SHARED_RESOURCES.update({
            "events": events,
            "embedding_provider": cached_embedding_provider,
            "llm_provider": llm_provider,
            "rag_service": rag_service,
            "offset_wells": offset_wells,
            "query_service": query_service,
        })
    return _SHARED_RESOURCES


def run_local_rag_demo():
    """
    Interactive demonstration of the complete in-memory RAG pipeline.
    """
    print("=" * 75)
    print("LOCAL IN-MEMORY RAG PIPELINE VERIFICATION & DEMO (STAGE 1–6)")
    print("=" * 75)
    print("Environment: Host (No PostgreSQL, No pgvector required)")
    print("Database Backend: 100% In-Memory (InMemorySemanticIndex + NumPy)")

    pipeline = get_shared_pipeline()
    events = pipeline["events"]
    query_service = pipeline["query_service"]
    offset_wells = pipeline["offset_wells"]

    print(f"Loaded {len(events)} synthetic historical events from nwis_mock_historical_events.json.\n")

    # -------------------------------------------------------------------------
    # TEST QUESTION 1: Broad Formation & Depth Query
    # -------------------------------------------------------------------------
    q1 = "What drilling problems happened around 2800 meters in Formation X?"
    print("=" * 75)
    print(f"TEST CASE 1: Broad Formation & Depth Query")
    print(f"User Question: \"{q1}\"")
    print("=" * 75)

    response1 = query_service.answer_query(
        question=q1,
        nearby_well_ids=offset_wells,
        top_k=5,
        generate_answer=True,
    )

    parsed_1 = response1.get("parsed_query", {})
    evidence_1 = response1.get("rag_evidence", [])
    answer_1 = response1.get("answer", "")

    print("\n1. Parsed Query Parameters:")
    print(json.dumps(parsed_1, indent=2))

    print(f"\n2. Retrieved RAG Evidence ({len(evidence_1)} records):")
    for idx, ev in enumerate(evidence_1, start=1):
        meta = ev.get("metadata", {})
        well = meta.get("well_id", "N/A")
        depth = meta.get("depth_m", "N/A")
        form = meta.get("formation", "N/A")
        event = meta.get("event_type", "N/A")
        sem = f"{ev.get('semantic_similarity', 0.0):.4f}"
        struct = f"{ev.get('structured_score', 0.0):.4f}"
        hybrid = f"{ev.get('hybrid_score', 0.0):.4f}"
        print(f"   [{idx}] Well: {well:<10} | Depth: {depth:>4} m | Formation: {form:<12} | "
              f"Event: {event:<20} | Sem: {sem} | Struct: {struct} | Hybrid: {hybrid}")

    print("\n3. Grounded Answer Output:")
    print("-" * 75)
    print(answer_1)
    print("-" * 75)

    # -------------------------------------------------------------------------
    # TEST QUESTION 2: Explicitly Constrained Query
    # -------------------------------------------------------------------------
    q2 = "Show stuck pipe events near 2810m in Formation X within 50m."
    print("\n" + "=" * 75)
    print(f"TEST CASE 2: Explicitly Constrained Query")
    print(f"User Question: \"{q2}\"")
    print("=" * 75)

    response2 = query_service.answer_query(
        question=q2,
        nearby_well_ids=offset_wells,
        top_k=5,
        generate_answer=True,
    )

    parsed_2 = response2.get("parsed_query", {})
    evidence_2 = response2.get("rag_evidence", [])
    answer_2 = response2.get("answer", "")

    print("\n1. Parsed Query Parameters:")
    print(json.dumps(parsed_2, indent=2))

    print(f"\n2. Retrieved RAG Evidence ({len(evidence_2)} records):")
    for idx, ev in enumerate(evidence_2, start=1):
        meta = ev.get("metadata", {})
        well = meta.get("well_id", "N/A")
        depth = meta.get("depth_m", "N/A")
        form = meta.get("formation", "N/A")
        event = meta.get("event_type", "N/A")
        sem = f"{ev.get('semantic_similarity', 0.0):.4f}"
        struct = f"{ev.get('structured_score', 0.0):.4f}"
        hybrid = f"{ev.get('hybrid_score', 0.0):.4f}"
        print(f"   [{idx}] Well: {well:<10} | Depth: {depth:>4} m | Formation: {form:<12} | "
              f"Event: {event:<20} | Sem: {sem} | Struct: {struct} | Hybrid: {hybrid}")

    print("\n3. Grounded Answer Output:")
    print("-" * 75)
    print(answer_2)
    print("-" * 75)


class TestLocalInMemoryRAGPipeline(unittest.TestCase):
    """
    Automated unittests verifying the complete in-memory RAG pipeline locally
    without PostgreSQL or pgvector dependencies.
    """

    @classmethod
    def setUpClass(cls):
        pipeline = get_shared_pipeline()
        cls.events = pipeline["events"]
        cls.embedding_provider = pipeline["embedding_provider"]
        cls.llm_provider = pipeline["llm_provider"]
        cls.rag_service = pipeline["rag_service"]
        cls.offset_wells = pipeline["offset_wells"]
        cls.query_service = pipeline["query_service"]

    def test_01_query1_retrieval_and_answer_format(self):
        """Verify: 'What drilling problems happened around 2800 meters in Formation X?'"""
        q = "What drilling problems happened around 2800 meters in Formation X?"
        resp = self.query_service.answer_query(
            question=q,
            nearby_well_ids=self.offset_wells,
            top_k=5,
            generate_answer=True,
        )

        parsed = resp.get("parsed_query", {})
        self.assertEqual(parsed.get("current_depth"), 2800)
        self.assertEqual(parsed.get("formation"), "Formation X")

        evidence = resp.get("rag_evidence", [])
        self.assertGreaterEqual(len(evidence), 1)

        # Verify retrieved events are in Formation X and around target depth
        top_meta = evidence[0]["metadata"]
        self.assertEqual(top_meta["formation"].lower(), "formation x")
        self.assertTrue(2700 <= top_meta["depth_m"] <= 2900)

        # Verify metadata preserves cause, mitigation, outcome
        self.assertIsNotNone(top_meta.get("cause"))
        self.assertIsNotNone(top_meta.get("mitigation"))
        self.assertIsNotNone(top_meta.get("outcome"))
        self.assertNotEqual(top_meta.get("cause"), "Not recorded")
        self.assertNotEqual(top_meta.get("mitigation"), "Not recorded")
        self.assertNotEqual(top_meta.get("outcome"), "Not recorded")

        # Verify answer format
        ans = resp.get("answer", "")
        self.assertIn("Historical Findings:", ans)
        self.assertIn("Historical Inference:", ans)
        self.assertIn("Well:", ans)
        self.assertIn("Depth:", ans)
        self.assertIn("Event:", ans)
        self.assertIn("Cause:", ans)
        self.assertIn("Mitigation:", ans)
        self.assertIn("Outcome:", ans)

    def test_02_query2_strict_constraints_and_answer_format(self):
        """Verify: 'Show stuck pipe events near 2810m in Formation X within 50m.'"""
        q = "Show stuck pipe events near 2810m in Formation X within 50m."
        resp = self.query_service.answer_query(
            question=q,
            nearby_well_ids=self.offset_wells,
            top_k=5,
            generate_answer=True,
        )

        parsed = resp.get("parsed_query", {})
        self.assertEqual(parsed.get("current_depth"), 2810)
        self.assertEqual(parsed.get("formation"), "Formation X")
        self.assertIn("stuck pipe", parsed.get("event_type", "").lower())
        self.assertEqual(parsed.get("depth_tolerance"), 50)

        evidence = resp.get("rag_evidence", [])
        self.assertGreaterEqual(len(evidence), 1)

        # Top event must be WELL_021 (2810m) or WELL_008 (2805m)
        top_meta = evidence[0]["metadata"]
        self.assertIn(top_meta["well_id"], ["WELL_021", "WELL_008"])
        self.assertEqual(top_meta["formation"].lower(), "formation x")
        self.assertTrue(2760 <= top_meta["depth_m"] <= 2860)
        self.assertEqual(top_meta["event_type"].lower(), "stuck pipe")
        self.assertIsNotNone(top_meta.get("cause"))
        self.assertIsNotNone(top_meta.get("mitigation"))
        self.assertIsNotNone(top_meta.get("outcome"))
        self.assertNotEqual(top_meta.get("cause"), "Not recorded")
        self.assertNotEqual(top_meta.get("mitigation"), "Not recorded")
        self.assertNotEqual(top_meta.get("outcome"), "Not recorded")

        # Verify answer format
        ans = resp.get("answer", "")
        self.assertIn("Historical Findings:", ans)
        self.assertIn("Historical Inference:", ans)
        self.assertIn("Well:", ans)
        self.assertIn("Depth:", ans)
        self.assertIn("Event:", ans)
        self.assertIn("Cause:", ans)
        self.assertIn("Mitigation:", ans)
        self.assertIn("Outcome:", ans)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Local In-Memory RAG Verification")
    parser.add_argument("--test-only", action="store_true", help="Run only automated unittests")
    args, unknown = parser.parse_known_args()

    if not args.test_only:
        run_local_rag_demo()
        print("\n" + "=" * 75)
        print("RUNNING AUTOMATED UNITTEST ASSERTIONS")
        print("=" * 75)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestLocalInMemoryRAGPipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    if not res.wasSuccessful():
        sys.exit(1)
