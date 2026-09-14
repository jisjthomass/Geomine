"""
Stage 7 Integration Test:
Verifies the complete pipeline flow:
Query -> LLMQueryParser -> PgVectorRetriever -> Hybrid Ranking -> ContextBuilder -> Gemini Answer Generator.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv() or os.path.join(PROJECT_ROOT, ".env"))

from src.rag import (
    BaseRetriever,
    PgVectorRetriever,
    PgVectorDatabaseClient,
    build_rag_context,
)
from src.llm import (
    LLMProvider,
    LLMQueryParser,
    HistoricalAnswerGenerator,
    HistoricalQueryService,
)


class MockIntegrationLLM(LLMProvider):
    """Deterministic LLM for query parsing and answer generation in integration tests."""

    def embed_text(self, text: str) -> list[float]:
        return [0.1] * 16

    def generate(self, prompt: str) -> str:
        if "Extract the following fields:" in prompt:
            return '{"current_depth": 2800, "formation": "Formation Alpha", "event_type": "Stuck Pipe", "depth_tolerance": 100}'
        well = "TEST_WELL_02" if "TEST_WELL_02" in prompt else "TEST_WELL_01"
        return (
            "Historical Findings:\n\n"
            f"Well: {well}\nDepth: 2800 m\nEvent: Stuck Pipe\nCause: Differential sticking\n"
            "Mitigation: Worked pipe\nOutcome: Pipe freed\n\n---\n\n"
            f"Historical Inference:\n\n"
            f"Stuck pipe was experienced in Formation Alpha at 2800m on {well}."
        )


class TestStage7PipelineIntegration(unittest.TestCase):
    """Verifies end-to-end coordination between QueryParser, PgVectorRetriever, ContextBuilder, and Generator."""

    def test_pipeline_wiring_with_pgvector_retriever(self):
        """Validates that PgVectorRetriever seamlessly plugs into HistoricalQueryService."""
        llm = MockIntegrationLLM()
        parser = LLMQueryParser(llm)

        # Mock DB client returning a valid record
        class StubDBClient:
            def is_available(self):
                return True

            def semantic_search(self, **kwargs):
                return {
                    "results": [
                        {
                            "event_id": 101,
                            "content": "Well: TEST_WELL_01\nDepth: 2800 m\nFormation: Formation Alpha\nEvent: Stuck Pipe\nCause: Differential sticking\nMitigation: Worked pipe\nOutcome: Pipe freed",
                            "well_id": "TEST_WELL_01",
                            "depth_m": 2800.0,
                            "formation": "Formation Alpha",
                            "event_type": "Stuck Pipe",
                            "report_id": "RPT-101",
                            "document_type": "historical_event",
                            "distance": 0.15,
                        }
                    ]
                }

        retriever = PgVectorRetriever(db_client=StubDBClient())
        self.assertIsInstance(retriever, BaseRetriever)

        # 1. Parse Query
        question = "What stuck pipe problems happened around 2800m in Formation Alpha?"
        parsed = parser.parse(question)
        self.assertEqual(parsed["current_depth"], 2800)
        self.assertEqual(parsed["formation"], "Formation Alpha")
        self.assertEqual(parsed["event_type"], "Stuck Pipe")

        # 2. Retrieve via PgVectorRetriever
        evidence = retriever.retrieve(
            query=question,
            provider=llm,  # Provider with embed_text
            current_depth=parsed["current_depth"],
            formation=parsed["formation"],
            depth_tolerance=parsed["depth_tolerance"],
            event_type=parsed["event_type"],
            nearby_well_ids=["TEST_WELL_01"],
            top_k=3,
        )
        self.assertEqual(len(evidence), 1)
        top_ev = evidence[0]
        self.assertIn("hybrid_score", top_ev)
        self.assertIn("structured_score", top_ev)
        self.assertIn("semantic_similarity", top_ev)
        self.assertAlmostEqual(top_ev["structured_score"], 1.0, places=4)

        # 3. Build RAG Context
        context = build_rag_context(evidence)
        self.assertIn("TEST_WELL_01", context)
        self.assertIn("Formation Alpha", context)

        # 4. Generate Grounded Answer
        generator = HistoricalAnswerGenerator(llm)
        answer = generator.generate_answer(question=question, rag_context=context)
        self.assertIn("Historical Findings:", answer)
        self.assertIn("Historical Inference:", answer)
        self.assertIn("TEST_WELL_01", answer)

    def test_historical_query_service_with_pgvector_backend(self):
        """Validates HistoricalQueryService end-to-end integration using RAGRetrievalService with pgvector backend."""
        from src.rag import RAGRetrievalService

        llm = MockIntegrationLLM()

        class StubDBClient:
            def is_available(self):
                return True

            def semantic_search(self, **kwargs):
                return {
                    "results": [
                        {
                            "event_id": 202,
                            "content": "Well: TEST_WELL_02\nDepth: 2800 m\nFormation: Formation Alpha\nEvent: Stuck Pipe\nCause: Differential sticking\nMitigation: Worked pipe\nOutcome: Pipe freed",
                            "well_id": "TEST_WELL_02",
                            "depth_m": 2800.0,
                            "formation": "Formation Alpha",
                            "event_type": "Stuck Pipe",
                            "report_id": "RPT-202",
                            "document_type": "historical_event",
                            "distance": 0.10,
                        }
                    ]
                }

        rag_service = RAGRetrievalService(
            provider=llm,
            backend="pgvector",
            db_client=StubDBClient(),
        )

        mock_events = [
            {
                "event_id": 202,
                "well_id": "TEST_WELL_02",
                "depth_m": 2800.0,
                "formation": "Formation Alpha",
                "event_type": "Stuck Pipe",
                "cause": "Differential sticking",
                "mitigation": "Worked pipe",
                "outcome": "Pipe freed",
            }
        ]

        query_service = HistoricalQueryService(
            provider=llm,
            events=mock_events,
            rag_service=rag_service,
        )

        response = query_service.answer_query(
            question="What stuck pipe problems happened around 2800m in Formation Alpha?",
            nearby_well_ids=["TEST_WELL_02"],
            top_k=3,
            generate_answer=True,
        )

        self.assertIn("parsed_query", response)
        self.assertIn("rag_evidence", response)
        self.assertGreaterEqual(len(response["rag_evidence"]), 1)
        self.assertIn("answer", response)
        self.assertIn("Historical Findings:", response["answer"])
        self.assertIn("TEST_WELL_02", response["answer"])

    def test_live_postgresql_pgvector_pipeline_integration(self):
        """End-to-end integration test querying the live PostgreSQL + pgvector database."""
        client = PgVectorDatabaseClient()
        if not client.is_available():
            self.skipTest("PostgreSQL + pgvector database is not available; skipping live database integration test.")

        import uuid
        run_id = uuid.uuid4().hex[:8].upper()
        test_well = f"TEST_WELL_STAGE7_{run_id}"

        # 1. Insert isolated test record into real PostgreSQL
        llm = MockIntegrationLLM()
        test_vec = llm.embed_text("Drill string stuck in Formation Alpha at 2800m")
        try:
            client.insert_event_embedding(
                event_id=9701,
                content=f"Well: {test_well}\nDepth: 2800 m\nFormation: Formation Alpha\nEvent: Stuck Pipe\nCause: Differential sticking\nMitigation: Worked pipe\nOutcome: Pipe freed",
                embedding=test_vec,
                well_id=test_well,
                depth_m=2800.0,
                formation="Formation Alpha",
                event_type="Stuck Pipe",
                report_id="RPT-9701",
            )

            # 2. Wire through RAGRetrievalService and HistoricalQueryService
            from src.rag import RAGRetrievalService
            rag_service = RAGRetrievalService(
                provider=llm,
                backend="pgvector",
                db_client=client,
            )

            mock_events = [
                {
                    "event_id": 9701,
                    "well_id": test_well,
                    "depth_m": 2800.0,
                    "formation": "Formation Alpha",
                    "event_type": "Stuck Pipe",
                    "cause": "Differential sticking",
                    "mitigation": "Worked pipe",
                    "outcome": "Pipe freed",
                }
            ]

            query_service = HistoricalQueryService(
                provider=llm,
                events=mock_events,
                rag_service=rag_service,
            )

            # 3. Execute query: Parser -> PgVectorRetriever -> Hybrid Ranking -> Context -> Answer
            response = query_service.answer_query(
                question="What stuck pipe problems happened around 2800m in Formation Alpha?",
                nearby_well_ids=[test_well],
                top_k=3,
                generate_answer=True,
            )

            # 4. Verify results
            self.assertIn("rag_evidence", response)
            self.assertGreaterEqual(len(response["rag_evidence"]), 1)
            matching = [r for r in response["rag_evidence"] if r.get("metadata", {}).get("well_id") == test_well]
            self.assertEqual(len(matching), 1)
            top_rec = matching[0]
            self.assertIn("hybrid_score", top_rec)
            self.assertIn("structured_score", top_rec)
            self.assertIn("semantic_similarity", top_rec)
            self.assertGreaterEqual(top_rec["structured_score"], 0.85)

            # 5. Verify generated answer has grounding
            self.assertIn("answer", response)
            self.assertIn("Historical Findings:", response["answer"])
            self.assertIn("Historical Inference:", response["answer"])

        finally:
            # 6. Clean up isolated test record from PostgreSQL
            try:
                if client.db_module and hasattr(client.db_module, "get_db_connection"):
                    conn = client.db_module.get_db_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM historical_event_embeddings WHERE well_id = %s;", (test_well,))
                    conn.commit()
                    cur.close()
                    conn.close()
            except Exception:
                pass


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStage7PipelineIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    if not res.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    main()

