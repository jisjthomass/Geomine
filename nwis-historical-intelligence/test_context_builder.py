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

from src.rag.context_builder import build_rag_context


class TestContextBuilder(unittest.TestCase):
    """
    Unit tests for build_rag_context verifying factual transformation,
    field preservation, missing field fallback, score exclusion, and edge cases.
    """

    def test_one_evidence_record(self):
        """Verify context building with a single evidence record."""
        evidence = [
            {
                "id": "EVT_001",
                "metadata": {
                    "well_id": "WELL_017",
                    "depth_m": 2780,
                    "formation": "Formation X",
                    "event_type": "Mud Loss",
                    "cause": "High permeability",
                    "mitigation": "Increased mud weight",
                    "outcome": "Losses controlled",
                    "report_id": "WCR_017_001",
                },
            }
        ]

        context = build_rag_context(evidence)

        self.assertIn("Historical Evidence 1:", context)
        self.assertIn("Well: WELL_017", context)
        self.assertIn("Depth: 2780 m", context)
        self.assertIn("Formation: Formation X", context)
        self.assertIn("Event: Mud Loss", context)
        self.assertIn("Cause: High permeability", context)
        self.assertIn("Mitigation: Increased mud weight", context)
        self.assertIn("Outcome: Losses controlled", context)
        self.assertIn("Report: WCR_017_001", context)

    def test_multiple_evidence_records(self):
        """Verify multiple records are enumerated and separated cleanly."""
        evidence = [
            {
                "metadata": {
                    "well_id": "WELL_001",
                    "depth_m": 2500,
                    "formation": "Formation A",
                    "event_type": "Stuck Pipe",
                    "cause": "Differential sticking",
                    "mitigation": "Spotted acid pill",
                    "outcome": "Freed pipe",
                    "report_id": "RPT_001",
                }
            },
            {
                "metadata": {
                    "well_id": "WELL_002",
                    "depth_m": 2600,
                    "formation": "Formation B",
                    "event_type": "Tight Hole",
                    "cause": "Swelling shale",
                    "mitigation": "Reamed section",
                    "outcome": "Drilling resumed",
                    "report_id": "RPT_002",
                }
            },
        ]

        context = build_rag_context(evidence)

        self.assertIn("Historical Evidence 1:", context)
        self.assertIn("Well: WELL_001", context)
        self.assertIn("Historical Evidence 2:", context)
        self.assertIn("Well: WELL_002", context)
        self.assertTrue(context.index("Historical Evidence 1:") < context.index("Historical Evidence 2:"))

    def test_field_preservation(self):
        """Verify exact field values are preserved without corruption."""
        evidence = [
            {
                "metadata": {
                    "well_id": "OFF-SHORE-99",
                    "depth_m": 3125.5,
                    "formation": "Krishna-Godavari Deep Sand",
                    "event_type": "Gas Kick",
                    "cause": "Overpressured gas sand",
                    "mitigation": "Circulated out gas via choke",
                    "outcome": "Well shut-in then killed safely",
                    "report_id": "DOR-2026-X8",
                }
            }
        ]

        context = build_rag_context(evidence)

        self.assertIn("Well: OFF-SHORE-99", context)
        self.assertIn("Depth: 3125.5 m", context)
        self.assertIn("Formation: Krishna-Godavari Deep Sand", context)
        self.assertIn("Event: Gas Kick", context)
        self.assertIn("Cause: Overpressured gas sand", context)
        self.assertIn("Mitigation: Circulated out gas via choke", context)
        self.assertIn("Outcome: Well shut-in then killed safely", context)
        self.assertIn("Report: DOR-2026-X8", context)

    def test_missing_fields_become_not_recorded(self):
        """Verify missing or null fields default to 'Not recorded' without throwing errors."""
        evidence = [
            {
                "metadata": {
                    "well_id": "WELL_EMPTY",
                    "depth_m": None,
                    "formation": None,
                    "event_type": "",
                    "cause": None,
                    "mitigation": None,
                    "outcome": None,
                    "report_id": None,
                }
            }
        ]

        context = build_rag_context(evidence)

        self.assertIn("Well: WELL_EMPTY", context)
        self.assertIn("Depth: Not recorded", context)
        self.assertIn("Formation: Not recorded", context)
        self.assertIn("Event: Not recorded", context)
        self.assertIn("Cause: Not recorded", context)
        self.assertIn("Mitigation: Not recorded", context)
        self.assertIn("Outcome: Not recorded", context)
        self.assertIn("Report: Not recorded", context)

    def test_max_results_limit(self):
        """Verify max_results parameter restricts output size."""
        evidence = [
            {"metadata": {"well_id": f"WELL_{i}", "depth_m": 2000 + i}}
            for i in range(10)
        ]

        context = build_rag_context(evidence, max_results=3)

        self.assertIn("Historical Evidence 1:", context)
        self.assertIn("Historical Evidence 2:", context)
        self.assertIn("Historical Evidence 3:", context)
        self.assertNotIn("Historical Evidence 4:", context)
        self.assertNotIn("WELL_3", context)

    def test_embeddings_and_scores_not_included(self):
        """Verify internal embeddings, similarity scores, and hybrid scores are excluded."""
        evidence = [
            {
                "id": "DOC_001",
                "text": "Internal text representation",
                "embedding": [0.123, 0.456, 0.789],
                "vector": [1.0, 0.0, 0.0],
                "hybrid_score": 0.897,
                "semantic_similarity": 0.945,
                "structured_score": 0.825,
                "metadata": {
                    "well_id": "WELL_017",
                    "depth_m": 2780,
                    "formation": "Formation X",
                    "event_type": "Mud Loss",
                },
            }
        ]

        context = build_rag_context(evidence)

        self.assertNotIn("0.897", context)
        self.assertNotIn("0.945", context)
        self.assertNotIn("0.825", context)
        self.assertNotIn("hybrid_score", context)
        self.assertNotIn("semantic_similarity", context)
        self.assertNotIn("structured_score", context)
        self.assertNotIn("embedding", context)
        self.assertNotIn("vector", context)

    def test_empty_evidence_behaves_safely(self):
        """Verify empty and None evidence return empty string safely."""
        self.assertEqual(build_rag_context([]), "")
        self.assertEqual(build_rag_context(None), "")
        self.assertEqual(build_rag_context([None, "not a dict"]), "")


def main():
    print("=" * 50)
    print("RUNNING CONTEXT BUILDER UNIT TESTS")
    print("=" * 50)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestContextBuilder)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("=" * 50)
        print("ALL CONTEXT BUILDER TESTS PASSED SUCCESSFULLY!")
        print("=" * 50)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
