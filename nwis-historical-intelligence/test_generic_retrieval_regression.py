import hashlib
import json
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

from src.rag.document_builder import events_to_documents
from src.rag.embeddings import EmbeddingProvider
from src.rag.hybrid_retrieval import (
    HybridRetriever,
    compute_structured_score,
    SEMANTIC_WEIGHT,
    STRUCTURED_WEIGHT,
)
from src.rag.retrieval_service import RAGRetrievalService
from src.llm import LLMProvider, HistoricalQueryService


from collections import Counter


class KeywordSemanticEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic embedding provider that projects text onto a vocabulary vector space.
    Word overlaps produce realistic cosine similarity scores without external API calls.
    """
    def __init__(self, vocab=None):
        self.vocab = vocab or [
            "well", "depth", "m", "formation", "x", "a", "b", "c", "y", "z",
            "stuck", "pipe", "mud", "loss", "lost", "circulation",
            "kick", "gas", "show", "wellbore", "instability", "torque", "spike",
            "rop", "reduction", "differential", "sticking", "problems", "incidents",
            "around", "at", "meters", "freed", "drilling", "resumed"
        ]
        self.dim = len(self.vocab)

    def embed_text(self, text: str) -> list[float]:
        if not isinstance(text, str):
            raise TypeError("Expected string text")
        words = text.lower().replace(":", " ").replace("-", " ").replace("_", " ").split()
        counts = Counter(words)
        vec = [float(counts.get(w, 0)) for w in self.vocab]
        for w in words:
            if w not in self.vocab:
                h = abs(hash(w)) % self.dim
                vec[h] += 0.5
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return [1.0 / math.sqrt(self.dim)] * self.dim
        return [x / norm for x in vec]


class TestGenericRetrievalRegression(unittest.TestCase):
    """
    Generic regression test suite validating the hybrid retrieval pipeline dynamically
    against arbitrary datasets without hardcoded values.
    """

    @classmethod
    def setUpClass(cls):
        dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
        with open(dataset_path, "r", encoding="utf-8") as f:
            cls.events = json.load(f)

        cls.provider = KeywordSemanticEmbeddingProvider()
        cls.documents = events_to_documents(cls.events)
        for doc in cls.documents:
            doc["embedding"] = cls.provider.embed_text(doc["text"])

        cls.retriever = HybridRetriever(documents=cls.documents)

    def test_constrained_depth_formation_event_query(self):
        """
        Dynamically derive ground-truth matches for depth + formation + event type
        and verify that the hybrid retriever ranks matching candidates at the top.
        """
        # Select target criteria dynamically from the first valid record
        seed = next(e for e in self.events if e.get("formation") and e.get("depth_m") and e.get("event_type"))
        target_formation = seed["formation"]
        target_depth = float(seed["depth_m"])
        target_event = seed["event_type"]
        tolerance = 100.0

        # Derive ground-truth records matching all three criteria
        full_matches = [
            e for e in self.events
            if str(e.get("formation", "")).lower() == target_formation.lower()
            and e.get("depth_m") is not None
            and abs(float(e["depth_m"]) - target_depth) <= tolerance
            and str(e.get("event_type", "")).lower() == target_event.lower()
        ]
        self.assertGreater(len(full_matches), 0, "Seed criteria must have at least one match")

        results = self.retriever.retrieve(
            query=f"Problems in {target_formation} around {target_depth}m with {target_event}",
            provider=self.provider,
            current_depth=target_depth,
            formation=target_formation,
            depth_tolerance=tolerance,
            event_type=target_event,
            top_k=5,
        )

        self.assertGreater(len(results), 0)

        # 1. Verify structured score of top result includes formation + depth + event (0.35 + 0.35 + 0.15 = 0.85 minimum)
        top_meta = results[0]["metadata"]
        top_struct_score = results[0]["structured_score"]
        self.assertGreaterEqual(top_struct_score, 0.85)

        # 2. Verify top result satisfies the ground-truth constraints
        self.assertEqual(str(top_meta.get("formation")).lower(), target_formation.lower())
        self.assertLessEqual(abs(float(top_meta.get("depth_m")) - target_depth), tolerance)
        self.assertEqual(str(top_meta.get("event_type")).lower(), target_event.lower())

        # 3. Verify hybrid score calculation consistency
        for res in results:
            cos_sim = res["semantic_similarity"]
            sem_norm = (cos_sim + 1.0) / 2.0
            expected_hybrid = SEMANTIC_WEIGHT * sem_norm + STRUCTURED_WEIGHT * res["structured_score"]
            self.assertAlmostEqual(res["hybrid_score"], expected_hybrid, places=5)

    def test_depth_and_formation_query(self):
        """
        Verify retrieval when only depth and formation are specified (event_type is None).
        """
        seed = next(e for e in self.events if e.get("formation") and e.get("depth_m"))
        target_formation = seed["formation"]
        target_depth = float(seed["depth_m"])
        tolerance = 100.0

        results = self.retriever.retrieve(
            query=f"Drilling events in {target_formation} near {target_depth}m",
            provider=self.provider,
            current_depth=target_depth,
            formation=target_formation,
            depth_tolerance=tolerance,
            event_type=None,
            top_k=5,
        )

        self.assertGreater(len(results), 0)
        # Any candidate matching both formation and depth within tolerance gets >= 0.70
        top_result = results[0]
        self.assertGreaterEqual(top_result["structured_score"], 0.70)
        self.assertEqual(str(top_result["metadata"].get("formation")).lower(), target_formation.lower())
        self.assertLessEqual(abs(float(top_result["metadata"].get("depth_m")) - target_depth), tolerance)

    def test_formation_only_query(self):
        """
        Verify retrieval when only formation is constrained (depth and event are None).
        """
        seed = next(e for e in self.events if e.get("formation"))
        target_formation = seed["formation"]

        results = self.retriever.retrieve(
            query=f"Incidents in {target_formation}",
            provider=self.provider,
            current_depth=None,
            formation=target_formation,
            event_type=None,
            top_k=5,
        )

        self.assertGreater(len(results), 0)
        for res in results:
            # All matching candidates should have at least the formation weight (+0.35)
            self.assertGreaterEqual(res["structured_score"], 0.35)
            self.assertEqual(str(res["metadata"].get("formation")).lower(), target_formation.lower())

    def test_event_type_only_semantic_query(self):
        """
        Verify retrieval when only event type is provided (no depth/formation).
        """
        seed = next(e for e in self.events if e.get("event_type"))
        target_event = seed["event_type"]

        results = self.retriever.retrieve(
            query=f"Issues involving {target_event}",
            provider=self.provider,
            current_depth=None,
            formation=None,
            event_type=target_event,
            top_k=5,
        )

        self.assertGreater(len(results), 0)
        # Documents matching event_type get structured score >= 0.15
        top_matches = [r for r in results if str(r["metadata"].get("event_type")).lower() == target_event.lower()]
        self.assertGreater(len(top_matches), 0)
        for match in top_matches:
            self.assertGreaterEqual(match["structured_score"], 0.15)

    def test_no_matching_structured_candidates_fallback(self):
        """
        Verify that when explicit structured constraints have zero matches, the retriever
        strictly returns zero results (no semantic leakage/fallback).
        Unconstrained general queries retrieve candidates.
        """
        # 1. Non-existent explicit constraints must return 0 results
        results = self.retriever.retrieve(
            query="General drilling hazard investigation",
            provider=self.provider,
            current_depth=999999.0,
            formation="UnobtainiumNonExistentFormation",
            depth_tolerance=10.0,
            event_type="HypotheticalAlienEvent",
            top_k=5,
        )
        self.assertEqual(len(results), 0)

        # 2. Genuinely unconstrained semantic query returns top_k candidates
        broad_results = self.retriever.retrieve(
            query="General drilling hazard investigation",
            provider=self.provider,
            current_depth=None,
            formation=None,
            event_type=None,
            top_k=5,
        )
        self.assertEqual(len(broad_results), 5)

    def test_empty_dataset(self):
        """
        Verify that an empty dataset behaves safely.
        """
        empty_retriever = HybridRetriever(documents=[])
        results = empty_retriever.retrieve(
            query="Test query",
            provider=self.provider,
            current_depth=2800,
            formation="Formation X",
            top_k=5,
        )
        self.assertEqual(results, [])

    def test_missing_optional_metadata(self):
        """
        Verify that records missing depth, formation, or event_type do not cause errors.
        """
        sparse_docs = [
            {"text": "Doc 1", "metadata": {}, "embedding": self.provider.embed_text("Doc 1")},
            {"text": "Doc 2", "metadata": {"well_id": "W1"}, "embedding": self.provider.embed_text("Doc 2")},
            {"text": "Doc 3", "metadata": {"depth_m": None, "formation": ""}, "embedding": self.provider.embed_text("Doc 3")},
        ]
        retriever = HybridRetriever(documents=sparse_docs)
        results = retriever.retrieve(
            query="Test query",
            provider=self.provider,
            current_depth=None,
            formation=None,
            event_type=None,
            top_k=3,
        )
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIn("hybrid_score", r)

    def test_different_depth_tolerances(self):
        """
        Verify that increasing depth tolerance includes candidates further away dynamically.
        """
        # Find two events in the same formation with known depth difference
        formations = {}
        for e in self.events:
            f = e.get("formation")
            d = e.get("depth_m")
            if f and d is not None:
                formations.setdefault(f, []).append(float(d))

        # Pick a formation with multiple distinct depths
        chosen_form = next(f for f, depths in formations.items() if len(set(depths)) >= 2)
        depths = sorted(list(set(formations[chosen_form])))
        d1, d2 = depths[0], depths[-1]
        diff = abs(d2 - d1)

        # Narrow tolerance strictly smaller than distance, broad tolerance strictly larger
        narrow_tol = diff * 0.5
        broad_tol = diff * 1.5

        score_narrow = compute_structured_score(
            metadata={"formation": chosen_form, "depth_m": d2},
            formation=chosen_form,
            current_depth=d1,
            depth_tolerance=narrow_tol,
        )
        score_broad = compute_structured_score(
            metadata={"formation": chosen_form, "depth_m": d2},
            formation=chosen_form,
            current_depth=d1,
            depth_tolerance=broad_tol,
        )

        self.assertGreater(score_broad, score_narrow)

    def test_case_insensitivity(self):
        """
        Verify that formation and event type matching is strictly case-insensitive.
        """
        seed = next(e for e in self.events if e.get("formation") and e.get("depth_m") and e.get("event_type"))
        form = seed["formation"]
        depth = float(seed["depth_m"])
        evt = seed["event_type"]

        res_upper = self.retriever.retrieve(
            query="test",
            provider=self.provider,
            current_depth=depth,
            formation=form.upper(),
            event_type=evt.upper(),
            top_k=5,
        )
        res_lower = self.retriever.retrieve(
            query="test",
            provider=self.provider,
            current_depth=depth,
            formation=form.lower(),
            event_type=evt.lower(),
            top_k=5,
        )

        self.assertEqual(len(res_upper), len(res_lower))
        for u, l in zip(res_upper, res_lower):
            self.assertAlmostEqual(u["structured_score"], l["structured_score"], places=5)
            self.assertAlmostEqual(u["hybrid_score"], l["hybrid_score"], places=5)

    def test_deterministic_ranking(self):
        """
        Verify that repeated executions produce identical ordering and scores.
        """
        query = "What stuck pipe problems happened?"
        res1 = self.retriever.retrieve(query=query, provider=self.provider, top_k=5)
        res2 = self.retriever.retrieve(query=query, provider=self.provider, top_k=5)

        self.assertEqual(len(res1), len(res2))
        for r1, r2 in zip(res1, res2):
            self.assertEqual(r1["text"], r2["text"])
            self.assertEqual(r1["hybrid_score"], r2["hybrid_score"])

    def test_dynamic_constraint_switch(self):
        """
        Verify that switching formation constraints dynamically switches the candidate set.
        """
        distinct_forms = list({e.get("formation") for e in self.events if e.get("formation")})
        self.assertGreaterEqual(len(distinct_forms), 2)
        form_a, form_b = distinct_forms[0], distinct_forms[1]

        res_a = self.retriever.retrieve(query="test", provider=self.provider, formation=form_a, top_k=3)
        res_b = self.retriever.retrieve(query="test", provider=self.provider, formation=form_b, top_k=3)

        for r in res_a:
            self.assertEqual(str(r["metadata"].get("formation")).lower(), form_a.lower())
        for r in res_b:
            self.assertEqual(str(r["metadata"].get("formation")).lower(), form_b.lower())

    def test_query_service_integration_pipeline(self):
        """
        Verify query parser to retrieval service coordination dynamically.
        """
        seed = next(e for e in self.events if e.get("formation") and e.get("depth_m"))
        form = seed["formation"]
        depth = int(seed["depth_m"])

        class DynamicMockParserLLM(LLMProvider):
            def generate(self, prompt: str) -> str:
                return json.dumps({
                    "current_depth": depth,
                    "formation": form,
                    "event_type": None,
                    "depth_tolerance": 100,
                })

        llm = DynamicMockParserLLM()
        rag_svc = RAGRetrievalService(events=self.events, provider=self.provider, auto_prepare=True)
        query_svc = HistoricalQueryService(provider=llm, events=self.events, rag_service=rag_svc)

        result = query_svc.answer_query(
            question=f"What happened at {depth}m in {form}?",
            nearby_well_ids=[seed["well_id"]] if seed.get("well_id") else None,
            top_k=3,
        )

        self.assertIn("rag_evidence", result)
        self.assertGreater(len(result["rag_evidence"]), 0)
        top_ev = result["rag_evidence"][0]
        self.assertIn("hybrid_score", top_ev)
        self.assertEqual(str(top_ev["metadata"].get("formation")).lower(), form.lower())


def main():
    print("=" * 60)
    print("RUNNING GENERIC RETRIEVAL REGRESSION TESTS")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGenericRetrievalRegression)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    if res.wasSuccessful():
        print("=" * 60)
        print("ALL GENERIC RETRIEVAL REGRESSION TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
