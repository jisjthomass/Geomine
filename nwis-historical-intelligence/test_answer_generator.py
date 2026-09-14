import os
import sys
import unittest

# Add project root and src to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.llm import LLMProvider, HistoricalAnswerGenerator
from src.rag import build_rag_context, RAGAnswerService


class MockProvider(LLMProvider):
    """
    Mock LLM provider that captures prompts and returns predefined text.
    """
    def __init__(self, canned_response: str = "Mock generated explanation."):
        self.canned_response = canned_response
        self.captured_prompt = None

    def generate(self, prompt: str) -> str:
        self.captured_prompt = prompt
        return self.canned_response


class TestAnswerGenerator(unittest.TestCase):
    """
    Unit tests for HistoricalAnswerGenerator and RAGAnswerService.
    """

    def test_grounded_answer_generation_with_rag_context(self):
        """
        Tests RAG-grounded answer generation with block formatting, verifying
        Historical Findings and Historical Inference prompt requirements.
        """
        mock_block_explanation = (
            "Historical Findings:\n\n"
            "Well: WELL_017\n"
            "Depth: 2780 m\n"
            "Event: Mud Loss\n"
            "Cause: High permeability\n"
            "Mitigation: Increased mud weight\n"
            "Outcome: Losses controlled\n\n"
            "---"
            "\n\n"
            "Historical Inference:\n"
            "The historical records for this depth interval and formation indicate localized permeability zones associated with mud loss."
        )

        provider = MockProvider(canned_response=mock_block_explanation)
        generator = HistoricalAnswerGenerator(provider=provider)

        question = "What drilling problems happened around 2780 meters in Formation X?"
        evidence = [
            {
                "metadata": {
                    "well_id": "WELL_017",
                    "depth_m": 2780,
                    "formation": "Formation X",
                    "event_type": "Mud Loss",
                    "cause": "High permeability",
                    "mitigation": "Increased mud weight",
                    "outcome": "Losses controlled",
                    "report_id": "WCR_017_001",
                }
            }
        ]
        rag_context = build_rag_context(evidence)

        answer = generator.generate_answer(question=question, rag_context=rag_context)

        self.assertEqual(answer, mock_block_explanation)
        prompt = provider.captured_prompt
        self.assertIsNotNone(prompt)

        # Verify user question and factual evidence presence
        self.assertIn(question, prompt)
        self.assertIn("WELL_017", prompt)
        self.assertIn("Mud Loss", prompt)
        self.assertIn("High permeability", prompt)
        self.assertIn("WCR_017_001", prompt)

        # Verify required section headers
        self.assertIn("Historical Findings:", prompt)
        self.assertIn("Historical Inference:", prompt)

        # Verify required block fields
        self.assertIn("Well:", prompt)
        self.assertIn("Depth:", prompt)
        self.assertIn("Event:", prompt)
        self.assertIn("Cause:", prompt)
        self.assertIn("Mitigation:", prompt)
        self.assertIn("Outcome:", prompt)
        self.assertIn("---", prompt)

        # Verify negative constraints and grounding rules
        self.assertTrue("Do NOT turn the evidence into paragraphs" in prompt or "paragraphs" in prompt)
        self.assertTrue("Do NOT make future predictions" in prompt or "future predictions" in prompt)
        self.assertTrue("Do NOT provide operational recommendations" in prompt or "recommendations" in prompt)
        self.assertTrue("No Disclaimers" in prompt or "disclaimers" in prompt)
        self.assertNotIn("Important:", prompt)

    def test_existing_behavior_without_rag_context(self):
        """
        Verifies that calling generate_answer without RAG context preserves the
        original concise summary instructions and JSON format without breakage.
        """
        canned = "Historically, 1 well experienced Mud Loss due to high permeability."
        provider = MockProvider(canned_response=canned)
        generator = HistoricalAnswerGenerator(provider=provider)

        question = "Summarize historical problems around 2780m in Formation X."
        historical_intel = {
            "historical_events": [{"well_id": "WELL_017", "event_type": "Mud Loss"}],
            "pattern_analysis": {"total_events": 1},
        }

        answer = generator.generate_answer(question=question, historical_intelligence=historical_intel)

        self.assertEqual(answer, canned)
        prompt = provider.captured_prompt
        self.assertIsNotNone(prompt)

        # Verify original system instructions used
        self.assertIn("VERY CONCISE, single-paragraph summary", prompt)
        self.assertIn("Maximum 3-4 sentences", prompt)
        self.assertIn(question, prompt)
        self.assertIn("HISTORICAL INTELLIGENCE DATA (SOURCE OF TRUTH)", prompt)

        # Verify RAG-specific instructions are NOT present in non-RAG call
        self.assertNotIn("Historical Findings:", prompt)
        self.assertNotIn("Historical Inference:", prompt)

    def test_empty_rag_context_handling(self):
        """
        Tests answer generation when RAG context is empty.
        """
        empty_canned_response = (
            "Historical Findings:\n"
            "No matching historical records found.\n\n"
            "Historical Inference:\n"
            "No historical offset incident patterns are available for the requested parameters."
        )

        provider = MockProvider(canned_response=empty_canned_response)
        generator = HistoricalAnswerGenerator(provider=provider)

        question = "What happened at 5000 meters in Formation NonExistent?"
        answer = generator.generate_answer(question=question, rag_context="")

        self.assertEqual(answer, empty_canned_response)
        prompt = provider.captured_prompt

        self.assertIn(question, prompt)
        self.assertIn("No matching historical records found.", prompt)
        self.assertIn("Historical Findings:", prompt)
        self.assertIn("Historical Inference:", prompt)

    def test_critical_grounding_constraint(self):
        """
        Stage 6 Critical Grounding Test: Verifies that the prompt contains the
        exact supplied evidence and instructs the model to stay strictly grounded.
        """
        provider = MockProvider()
        generator = HistoricalAnswerGenerator(provider=provider)

        evidence = [
            {
                "metadata": {
                    "well_id": "TEST-001",
                    "depth_m": 2800,
                    "formation": "Formation X",
                    "event_type": "Stuck Pipe",
                    "cause": "Differential sticking",
                    "mitigation": "Worked pipe",
                    "outcome": "Pipe freed",
                    "report_id": "RPT-TEST-001",
                }
            }
        ]
        context = build_rag_context(evidence)
        question = "What happened around 2800m?"

        generator.generate_answer(question=question, rag_context=context)
        prompt = provider.captured_prompt

        # 1. Verify prompt contains all exact supplied fields
        self.assertIn("TEST-001", prompt)
        self.assertIn("2800", prompt)
        self.assertIn("Formation X", prompt)
        self.assertIn("Stuck Pipe", prompt)
        self.assertIn("Differential sticking", prompt)
        self.assertIn("Worked pipe", prompt)
        self.assertIn("Pipe freed", prompt)

        # 2. Verify strict grounding instructions
        self.assertIn("Use ONLY the supplied historical evidence to make factual claims", prompt)
        self.assertIn("Do NOT invent", prompt)
        self.assertIn("Do NOT make future predictions", prompt)
        self.assertIn("Do NOT provide operational recommendations", prompt)

    def test_rag_answer_service_coordination(self):
        """
        Verifies RAGAnswerService translates raw evidence through build_rag_context
        and invokes the generator properly.
        """
        provider = MockProvider(canned_response="Historical Findings:\n...")
        generator = HistoricalAnswerGenerator(provider=provider)
        service = RAGAnswerService(answer_generator=generator, max_evidence=2)

        evidence = [
            {"metadata": {"well_id": "WELL_A", "depth_m": 1500, "event_type": "Loss"}},
            {"metadata": {"well_id": "WELL_B", "depth_m": 1600, "event_type": "Kick"}},
            {"metadata": {"well_id": "WELL_C", "depth_m": 1700, "event_type": "Stuck"}},
        ]

        service.generate_answer("Incident summary?", evidence)
        prompt = provider.captured_prompt

        self.assertIn("WELL_A", prompt)
        self.assertIn("WELL_B", prompt)
        # WELL_C excluded because max_evidence=2
        self.assertNotIn("WELL_C", prompt)


def main():
    print("=" * 50)
    print("RUNNING HISTORICAL ANSWER GENERATOR UNIT TESTS")
    print("=" * 50)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnswerGenerator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("=" * 50)
        print("ALL ANSWER GENERATOR TESTS PASSED SUCCESSFULLY!")
        print("=" * 50)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
