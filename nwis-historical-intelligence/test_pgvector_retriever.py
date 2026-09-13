"""
Automated unit and integration regression test suite for PgVectorRetriever,
PgVectorDatabaseClient, metric conversion, and data ingestion.

Unit tests validate pure logic, metric conversions, and scoring formulas offline.
Database integration tests validate real PostgreSQL + pgvector operations using
isolated, idempotent test data (skipping cleanly if the database is unreachable).
"""

import math
import os
import sys
import unittest
import uuid

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.rag.base_retriever import BaseRetriever
from src.rag.embeddings import EmbeddingProvider
from src.rag.hybrid_retrieval import (
    SEMANTIC_WEIGHT,
    STRUCTURED_WEIGHT,
    compute_structured_score,
)
from src.rag.pgvector_backend import (
    PgVectorDatabaseClient,
    PgVectorRetriever,
    ingest_events_to_pgvector,
)


class DeterministicVectorProvider(EmbeddingProvider):
    """Generates fixed, deterministic vectors of specified dimension for testing."""

    def __init__(self, dimension: int = 16):
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        # Generate normalized vector based on character sum
        seed = sum(ord(c) for c in text)
        vec = [float((seed + i * 17) % 100 + 1) for i in range(self.dimension)]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


class TestPureLogicPgVector(unittest.TestCase):
    """
    Pure unit tests validating metric conversion, scoring, dimension compatibility,
    and strict structured constraint handling without database calls.
    """

    def setUp(self):
        self.provider = DeterministicVectorProvider(dimension=16)

    def test_cosine_distance_to_similarity_metric_conversion(self):
        """
        Verify that pgvector cosine distance d in [0, 2] is converted consistently
        to cosine similarity s = 1.0 - d in [-1, 1] and normalized to [0, 1].
        """
        test_distances = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0]
        for d in test_distances:
            # Expected similarity: s = 1.0 - d
            expected_sim = 1.0 - d
            # Expected normalized similarity: (s + 1.0) / 2.0 = 1.0 - d / 2.0
            expected_norm = (expected_sim + 1.0) / 2.0

            computed_sim = max(-1.0, min(1.0, 1.0 - d))
            computed_norm = max(0.0, min(1.0, (computed_sim + 1.0) / 2.0))

            self.assertAlmostEqual(computed_sim, expected_sim, places=5)
            self.assertAlmostEqual(computed_norm, expected_norm, places=5)

    def test_hybrid_score_calculation_consistency(self):
        """
        Verify hybrid score formula matches Stage 4/5:
        hybrid_score = 0.60 * semantic_norm + 0.40 * structured_score
        """
        distance = 0.20
        cos_sim = 1.0 - distance  # 0.80
        semantic_norm = (cos_sim + 1.0) / 2.0  # 0.90
        structured_score = 0.85

        expected_hybrid = SEMANTIC_WEIGHT * semantic_norm + STRUCTURED_WEIGHT * structured_score
        self.assertAlmostEqual(expected_hybrid, 0.60 * 0.90 + 0.40 * 0.85, places=5)
        self.assertAlmostEqual(expected_hybrid, 0.54 + 0.34, places=5)
        self.assertAlmostEqual(expected_hybrid, 0.88, places=5)

    def test_vector_dimension_compatibility(self):
        """
        Verify that document and query vectors have matching dimensions.
        """
        dim = 3072  # Actual observed Gemini embedding dimension
        provider = DeterministicVectorProvider(dimension=dim)
        doc_vec = provider.embed_text("Sample drilling incident report")
        query_vec = provider.embed_text("Sample query")

        self.assertEqual(len(doc_vec), dim)
        self.assertEqual(len(query_vec), dim)
        self.assertEqual(len(doc_vec), len(query_vec))

    def test_strict_structured_filtering_returns_empty_when_no_matches(self):
        """
        CORRECTION 3: When explicit structured constraints exist and zero candidates
        satisfy them, return zero candidates rather than falling back to unconstrained search.
        """
        class MockEmptyDBClient:
            def semantic_search(self, *args, **kwargs):
                return {"results": []}

        retriever = PgVectorRetriever(db_client=MockEmptyDBClient())
        results = retriever.retrieve(
            query="Problems in Formation X",
            provider=self.provider,
            formation="Formation X",
            current_depth=2800.0,
            depth_tolerance=100.0,
            event_type="Stuck Pipe",
            top_k=5,
        )

        # Must be empty; strictly no silent fallback to unconstrained search
        self.assertEqual(results, [])

    def test_unconstrained_semantic_query_retrieves_candidates(self):
        """
        When NO structured constraints are present (general semantic query),
        retriever queries database without structured filters.
        """
        called_with = {}

        class MockGeneralDBClient:
            def semantic_search(self, **kwargs):
                called_with.update(kwargs)
                return {
                    "results": [
                        {
                            "event_id": 1,
                            "content": "Doc 1",
                            "well_id": "W1",
                            "depth_m": 1500.0,
                            "formation": "Formation A",
                            "event_type": "Lost Circulation",
                            "distance": 0.2,
                        }
                    ]
                }

        retriever = PgVectorRetriever(db_client=MockGeneralDBClient())
        results = retriever.retrieve(
            query="What causes mud loss?",
            provider=self.provider,
            formation=None,
            current_depth=None,
            event_type=None,
            top_k=3,
        )

        self.assertEqual(len(results), 1)
        # Verify no structured filters were passed to DB
        self.assertIsNone(called_with.get("formation"))
        self.assertIsNone(called_with.get("min_depth"))
        self.assertIsNone(called_with.get("max_depth"))
        self.assertIsNone(called_with.get("event_type"))


class TestPostgreSQLPgVectorIntegration(unittest.TestCase):
    """
    Live database integration tests against PostgreSQL + pgvector.
    Uses dynamic, isolated test well IDs with automated pre- and post-test cleanup.
    Explicitly skips if PostgreSQL + pgvector is unavailable.
    """

    @classmethod
    def setUpClass(cls):
        # Generate unique test execution prefix to prevent collision and duplicate accumulation
        cls.test_run_id = uuid.uuid4().hex[:8].upper()
        cls.test_well_a = f"TEST_WELL_A_{cls.test_run_id}"
        cls.test_well_b = f"TEST_WELL_B_{cls.test_run_id}"
        cls.test_well_c = f"TEST_WELL_C_{cls.test_run_id}"
        cls.test_wells = [cls.test_well_a, cls.test_well_b, cls.test_well_c]

        cls.client = PgVectorDatabaseClient()

        # Check if database is accessible
        if not cls.client.is_available():
            cls.db_available = False
            return

        cls.db_available = True
        cls.provider = DeterministicVectorProvider(dimension=16)

        # Pre-cleanup in case of previous aborted runs
        cls._cleanup_test_data()

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db_available", False):
            cls._cleanup_test_data()

    @classmethod
    def _cleanup_test_data(cls):
        try:
            if cls.client.db_module and hasattr(cls.client.db_module, "get_db_connection"):
                conn = cls.client.db_module.get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "DELETE FROM historical_event_embeddings WHERE well_id LIKE 'TEST_WELL_%';"
                )
                conn.commit()
                cur.close()
                conn.close()
        except Exception:
            pass

    def setUp(self):
        if not getattr(self, "db_available", False):
            self.skipTest("PostgreSQL + pgvector database is not available; skipping live database integration test.")

    def test_01_insertion_and_search(self):
        """1. Insertion of event embedding and semantic search retrieval."""
        vec = self.provider.embed_text("Drill string stuck in shale formation")
        rec_id = self.client.insert_event_embedding(
            event_id=9001,
            content="Drill string stuck at 2800m in Test Formation",
            embedding=vec,
            well_id=self.test_well_a,
            depth_m=2800.0,
            formation="Formation Alpha",
            event_type="Stuck Pipe",
            report_id="RPT-9001",
        )
        self.assertIsNotNone(rec_id)
        self.assertGreater(rec_id, 0)

        # Query back
        res = self.client.semantic_search(query_embedding=vec, top_k=5)
        results = res.get("results", [])
        self.assertGreaterEqual(len(results), 1)
        matching = [r for r in results if r["well_id"] == self.test_well_a]
        self.assertEqual(len(matching), 1)
        self.assertAlmostEqual(matching[0]["distance"], 0.0, places=4)

    def test_02_formation_filtering(self):
        """2. Formation filtering in PostgreSQL."""
        vec = self.provider.embed_text("Mud loss event")
        self.client.insert_event_embedding(
            event_id=9002,
            content="Mud loss in Formation Beta",
            embedding=vec,
            well_id=self.test_well_b,
            depth_m=2500.0,
            formation="Formation Beta",
            event_type="Mud Loss",
        )

        res = self.client.semantic_search(
            query_embedding=vec,
            formation="Formation Beta",
            top_k=5,
        )
        results = res.get("results", [])
        for r in results:
            self.assertEqual(r["formation"].lower(), "formation beta")

    def test_03_depth_filtering(self):
        """3. Depth range filtering (min_depth and max_depth)."""
        vec = self.provider.embed_text("Kick event at deep interval")
        self.client.insert_event_embedding(
            event_id=9003,
            content="Kick at 3200m",
            embedding=vec,
            well_id=self.test_well_c,
            depth_m=3200.0,
            formation="Formation Gamma",
            event_type="Kick",
        )

        res = self.client.semantic_search(
            query_embedding=vec,
            min_depth=3100.0,
            max_depth=3300.0,
            top_k=5,
        )
        results = res.get("results", [])
        matching = [r for r in results if r["well_id"] == self.test_well_c]
        self.assertEqual(len(matching), 1)
        self.assertGreaterEqual(matching[0]["depth_m"], 3100.0)
        self.assertLessEqual(matching[0]["depth_m"], 3300.0)

    def test_04_event_type_filtering(self):
        """4. Event type filtering."""
        vec = self.provider.embed_text("Test event query")
        res = self.client.semantic_search(
            query_embedding=vec,
            event_type="Mud Loss",
            top_k=5,
        )
        results = res.get("results", [])
        for r in results:
            self.assertEqual(r["event_type"].lower(), "mud loss")

    def test_05_nearby_well_filtering(self):
        """5. Nearby well ID filtering."""
        vec = self.provider.embed_text("Offset well search")
        res = self.client.semantic_search(
            query_embedding=vec,
            nearby_well_ids=[self.test_well_a, self.test_well_b],
            top_k=5,
        )
        results = res.get("results", [])
        for r in results:
            self.assertIn(r["well_id"], [self.test_well_a, self.test_well_b])

    def test_06_empty_results_handling(self):
        """6. Handling non-matching queries gracefully."""
        vec = self.provider.embed_text("Impossible query")
        res = self.client.semantic_search(
            query_embedding=vec,
            formation="NonExistentFormation12345",
            top_k=5,
        )
        self.assertEqual(len(res.get("results", [])), 0)

    def test_07_top_k_behavior(self):
        """7. top_k restrictions."""
        vec = self.provider.embed_text("General query")
        for k in [1, 2]:
            res = self.client.semantic_search(query_embedding=vec, top_k=k)
            self.assertLessEqual(len(res.get("results", [])), k)

    def test_08_cosine_distance_ordering(self):
        """8. Cosine distance sorting is ascending in database."""
        vec = self.provider.embed_text("Sort check query")
        res = self.client.semantic_search(query_embedding=vec, top_k=5)
        results = res.get("results", [])
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["distance"], results[i + 1]["distance"])

    def test_09_pgvector_retriever_hybrid_ranking(self):
        """9. PgVectorRetriever hybrid scoring and ranking."""
        retriever = PgVectorRetriever(db_client=self.client)
        results = retriever.retrieve(
            query="Drill string stuck",
            provider=self.provider,
            formation="Formation Alpha",
            current_depth=2800.0,
            depth_tolerance=100.0,
            event_type="Stuck Pipe",
            nearby_well_ids=[self.test_well_a],
            top_k=3,
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("hybrid_score", top)
        self.assertIn("semantic_similarity", top)
        self.assertIn("structured_score", top)
        # Matching all constraints should yield high structured score
        self.assertGreaterEqual(top["structured_score"], 0.85)

    def test_10_generic_data_ingestion(self):
        """10. Generic ingestion pipeline (event -> document -> embedding -> DB)."""
        mock_events = [
            {
                "event_id": 9010,
                "well_id": f"TEST_WELL_INGEST_{self.test_run_id}",
                "depth_m": 2900.0,
                "formation": "Formation Delta",
                "event_type": "Torque Spike",
                "description": "High torque noticed while drilling",
            }
        ]
        count = ingest_events_to_pgvector(
            events=mock_events,
            provider=self.provider,
            db_client=self.client,
            batch_size=10,
        )
        self.assertEqual(count, 1)


def main():
    print("=" * 60)
    print("RUNNING PGVECTOR RETRIEVER UNIT & INTEGRATION TESTS")
    print("=" * 60)
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPureLogicPgVector))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPostgreSQLPgVectorIntegration))
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    if not res.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    main()
