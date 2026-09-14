"""
Regression test suite specifically verifying dynamic hard eligibility filtering:
1. Explicit query with event_type + formation + depth returns ONLY records satisfying ALL THREE constraints.
2. Semantically similar records with the wrong formation are strictly excluded.
3. Semantically similar records outside depth tolerance are strictly excluded.
4. Broad queries without constraints still retrieve multiple relevant event types and formations.
5. Verification against the actual mock historical events dataset.
"""

import json
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.rag.embeddings import EmbeddingProvider
from src.rag.hybrid_retrieval import HybridRetriever, matches_dynamic_constraints, filter_candidates
from src.rag.document_builder import events_to_documents


class MockVectorProvider(EmbeddingProvider):
    """Deterministic embedding provider for testing."""
    def __init__(self, query_vec=None):
        self.query_vec = query_vec or [1.0, 0.0, 0.0]

    def embed_text(self, text: str) -> list[float]:
        return list(self.query_vec)


class TestHardConstraintsDynamicFiltering(unittest.TestCase):
    def setUp(self):
        self.provider = MockVectorProvider(query_vec=[1.0, 0.0, 0.0])
        # Synthetic documents to test boundary conditions
        self.docs = [
            # Doc 1: Satisfies ALL 3 (Stuck Pipe, Formation X, 2810m) - cos_sim = 0.8
            {
                "text": "Well: WELL_A\nDepth: 2810 m\nFormation: Formation X\nEvent: Stuck Pipe",
                "metadata": {
                    "well_id": "WELL_A",
                    "depth_m": 2810.0,
                    "formation": "Formation X",
                    "event_type": "Stuck Pipe",
                },
                "embedding": [0.8, 0.6, 0.0],
            },
            # Doc 2: Satisfies ALL 3 (Stuck Pipe, Formation X, 2805m within 100m tol) - cos_sim = 0.7
            {
                "text": "Well: WELL_B\nDepth: 2805 m\nFormation: Formation X\nEvent: Stuck Pipe",
                "metadata": {
                    "well_id": "WELL_B",
                    "depth_m": 2805.0,
                    "formation": "Formation X",
                    "event_type": "Stuck Pipe",
                },
                "embedding": [0.7, 0.71, 0.0],
            },
            # Doc 3: WRONG FORMATION (Formation C), but identical depth & event, HIGHER cos_sim = 1.0
            {
                "text": "Well: WELL_C\nDepth: 2810 m\nFormation: Formation C\nEvent: Stuck Pipe",
                "metadata": {
                    "well_id": "WELL_C",
                    "depth_m": 2810.0,
                    "formation": "Formation C",
                    "event_type": "Stuck Pipe",
                },
                "embedding": [1.0, 0.0, 0.0],
            },
            # Doc 4: OUTSIDE DEPTH TOLERANCE (2605m < 2710m), correct formation & event, HIGHER cos_sim = 1.0
            {
                "text": "Well: WELL_D\nDepth: 2605 m\nFormation: Formation X\nEvent: Stuck Pipe",
                "metadata": {
                    "well_id": "WELL_D",
                    "depth_m": 2605.0,
                    "formation": "Formation X",
                    "event_type": "Stuck Pipe",
                },
                "embedding": [1.0, 0.0, 0.0],
            },
            # Doc 5: WRONG EVENT TYPE (Differential Sticking), correct formation & depth, HIGHER cos_sim = 1.0
            {
                "text": "Well: WELL_E\nDepth: 2810 m\nFormation: Formation X\nEvent: Differential Sticking",
                "metadata": {
                    "well_id": "WELL_E",
                    "depth_m": 2810.0,
                    "formation": "Formation X",
                    "event_type": "Differential Sticking",
                },
                "embedding": [1.0, 0.0, 0.0],
            },
            # Doc 6: COMPLETELY DIFFERENT (Mud Loss, Formation Z, 1500m)
            {
                "text": "Well: WELL_F\nDepth: 1500 m\nFormation: Formation Z\nEvent: Mud Loss",
                "metadata": {
                    "well_id": "WELL_F",
                    "depth_m": 1500.0,
                    "formation": "Formation Z",
                    "event_type": "Mud Loss",
                },
                "embedding": [0.0, 1.0, 0.0],
            },
        ]
        self.retriever = HybridRetriever(documents=self.docs)

    def test_explicit_query_satisfies_all_three_constraints(self):
        """
        Requirement 11: An explicit query with event_type + formation + depth returns
        ONLY records satisfying ALL THREE constraints.
        """
        results = self.retriever.retrieve(
            query="stuck pipe in Formation X near 2810m",
            provider=self.provider,
            formation="Formation X",
            current_depth=2810.0,
            depth_tolerance=100.0,
            event_type="Stuck Pipe",
            top_k=10,
        )

        # Only WELL_A (2810m) and WELL_B (2805m) satisfy all 3
        returned_wells = [r["metadata"]["well_id"] for r in results]
        self.assertEqual(set(returned_wells), {"WELL_A", "WELL_B"})

        for r in results:
            self.assertEqual(r["metadata"]["event_type"], "Stuck Pipe")
            self.assertEqual(r["metadata"]["formation"], "Formation X")
            self.assertGreaterEqual(r["metadata"]["depth_m"], 2710.0)
            self.assertLessEqual(r["metadata"]["depth_m"], 2910.0)

    def test_semantically_similar_wrong_formation_excluded(self):
        """
        Requirement 12: A semantically similar record with the wrong formation
        is strictly excluded by the hard filter, even if cosine similarity is 1.0.
        """
        results = self.retriever.retrieve(
            query="stuck pipe in Formation X near 2810m",
            provider=self.provider,
            formation="Formation X",
            current_depth=2810.0,
            depth_tolerance=100.0,
            event_type="Stuck Pipe",
            top_k=10,
        )

        returned_wells = [r["metadata"]["well_id"] for r in results]
        self.assertNotIn("WELL_C", returned_wells, "Record with wrong formation (Formation C) must be excluded")

    def test_semantically_similar_outside_depth_tolerance_excluded(self):
        """
        Requirement 13: A semantically similar record outside the depth tolerance
        is strictly excluded, even if cosine similarity is 1.0.
        """
        results = self.retriever.retrieve(
            query="stuck pipe in Formation X near 2810m",
            provider=self.provider,
            formation="Formation X",
            current_depth=2810.0,
            depth_tolerance=100.0,
            event_type="Stuck Pipe",
            top_k=10,
        )

        returned_wells = [r["metadata"]["well_id"] for r in results]
        self.assertNotIn("WELL_D", returned_wells, "Record outside depth tolerance (2605m) must be excluded")

    def test_broad_query_without_constraints_retrieves_multiple_types_and_formations(self):
        """
        Requirement 14: Broad queries without those constraints still retrieve
        multiple relevant event types and formations as appropriate.
        """
        results = self.retriever.retrieve(
            query="drilling events",
            provider=self.provider,
            formation=None,
            current_depth=None,
            event_type=None,
            top_k=10,
        )

        # Should retrieve multiple events across different types and formations
        event_types = {r["metadata"]["event_type"] for r in results}
        formations = {r["metadata"]["formation"] for r in results}

        self.assertGreaterEqual(len(event_types), 3, "Broad query should return multiple event types")
        self.assertGreaterEqual(len(formations), 3, "Broad query should return multiple formations")

    def test_zero_results_when_no_records_satisfy_all_constraints(self):
        """
        Requirement 7: If no records satisfy all explicit constraints,
        return zero results rather than semantically similar fallbacks.
        """
        results = self.retriever.retrieve(
            query="stuck pipe at 5000m in Formation X",
            provider=self.provider,
            formation="Formation X",
            current_depth=5000.0,
            depth_tolerance=50.0,
            event_type="Stuck Pipe",
            top_k=5,
        )
        self.assertEqual(results, [], "Must return empty list when no records satisfy explicit constraints")

    def test_fully_dynamic_no_hardcoding(self):
        """
        Requirement 4: Filtering works dynamically for ANY arbitrary event, formation, or depth.
        """
        dynamic_doc = {
            "text": "Custom",
            "metadata": {
                "well_id": "DYNAMIC_001",
                "depth_m": 4321.0,
                "formation": "NonStandardLithology",
                "event_type": "RareAnomaly",
            },
            "embedding": [1.0, 0.0, 0.0],
        }
        retriever = HybridRetriever(documents=self.docs + [dynamic_doc])
        results = retriever.retrieve(
            query="Rare anomaly in NonStandardLithology",
            provider=self.provider,
            formation="NonStandardLithology",
            current_depth=4320.0,
            depth_tolerance=10.0,
            event_type="RareAnomaly",
            top_k=5,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"]["well_id"], "DYNAMIC_001")

    def test_mock_historical_events_dataset_verification(self):
        """
        Verify against the actual nwis_mock_historical_events.json:
        Query: 'Were there any stuck pipe events near 2810 meters in Formation X?'
        Constraints:
          - event_type = Stuck Pipe
          - formation = Formation X
          - depth = 2810 m, depth_tolerance = 100 m (range: 2710 - 2910 m)
        Expected eligible wells in dataset: ONLY WELL_021 (2810m) and WELL_008 (2805m).
        Specifically verify WELL_003 (2605m), WELL_018 (2640m), and WELL_019 (Formation C) are excluded.
        """
        dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw_events = json.load(f)

        cache_path = os.path.join(PROJECT_ROOT, "nwis_mock_embeddings_cache.json")
        cached_embeddings = {}
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_embeddings = json.load(f)

        docs = events_to_documents(raw_events)
        for d in docs:
            txt = d["text"]
            if txt in cached_embeddings:
                d["embedding"] = cached_embeddings[txt]
            else:
                d["embedding"] = [1.0, 0.0, 0.0]

        sample_dim = len(next(iter(cached_embeddings.values()))) if cached_embeddings else 3072
        query_vec = [1.0] + [0.0] * (sample_dim - 1)
        query_provider = MockVectorProvider(query_vec=query_vec)
        retriever = HybridRetriever(documents=docs)

        results = retriever.retrieve(
            query="Were there any stuck pipe events near 2810 meters in Formation X?",
            provider=query_provider,
            formation="Formation X",
            current_depth=2810.0,
            depth_tolerance=100.0,
            event_type="Stuck Pipe",
            top_k=10,
        )

        # Must have exactly 2 matching records in the entire dataset
        self.assertEqual(len(results), 2)
        returned_wells = {r["metadata"]["well_id"] for r in results}
        self.assertEqual(returned_wells, {"WELL_021", "WELL_008"})

        # Explicitly verify excluded wells
        self.assertNotIn("WELL_003", returned_wells, "WELL_003 (2605m) is outside depth range and must be excluded")
        self.assertNotIn("WELL_018", returned_wells, "WELL_018 (2640m) is outside depth range and must be excluded")
        self.assertNotIn("WELL_019", returned_wells, "WELL_019 (Formation C) has wrong formation and must be excluded")

        # Verify every returned record satisfies all constraints
        for r in results:
            self.assertEqual(r["metadata"]["event_type"], "Stuck Pipe")
            self.assertEqual(r["metadata"]["formation"], "Formation X")
            self.assertGreaterEqual(r["metadata"]["depth_m"], 2710.0)
            self.assertLessEqual(r["metadata"]["depth_m"], 2910.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
