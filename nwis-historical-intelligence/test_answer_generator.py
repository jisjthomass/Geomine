import os
import sys

# Add project root and src to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.llm import LLMProvider, HistoricalAnswerGenerator


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


def test_standard_answer_generation():
    """
    Tests answer generation with a realistic historical intelligence payload and block formatting.
    """
    mock_block_explanation = (
        "Historical Findings:\n\n"
        "Well: WELL_017\n"
        "Depth: 2780 m\n"
        "Event: Mud Loss\n"
        "Cause: High permeability\n"
        "Mitigation: Increased mud weight\n"
        "Outcome: Losses controlled\n\n"
        "Historical Inference:\n"
        "The historical records for this depth interval and formation indicate localized permeability zones associated with mud loss."
    )

    provider = MockProvider(canned_response=mock_block_explanation)
    generator = HistoricalAnswerGenerator(provider=provider)

    question = "What drilling problems happened around 2780 meters in Formation X?"
    historical_intelligence = {
        "historical_events": [
            {
                "well_id": "WELL_017",
                "depth_m": 2780,
                "formation": "Formation X",
                "event_type": "Mud Loss",
                "cause": "High permeability",
                "mitigation": "Increased mud weight",
                "outcome": "Losses controlled",
                "report_id": "WCR_017_001",
            }
        ],
        "pattern_analysis": {
            "total_events": 1,
            "unique_wells": 1,
            "most_common_event": "Mud Loss",
        },
        "evidence": [
            {
                "well_id": "WELL_017",
                "event_type": "Mud Loss",
                "event_depth_m": 2780,
                "depth_difference_m": 0,
                "relevance_score": 100,
                "reason": "Same formation and event occurred at the current depth.",
                "cause": "High permeability",
                "mitigation": "Increased mud weight",
                "outcome": "Losses controlled",
                "source": "WCR_017_001",
            }
        ],
    }

    print("[TEST 1] Testing answer generation with block format for populated intelligence payload:")
    answer = generator.generate_answer(question=question, historical_intelligence=historical_intelligence)

    # 1. Verify response matches MockProvider canned response
    assert answer == mock_block_explanation, "Generator output must match provider output."

    prompt = provider.captured_prompt
    assert prompt is not None, "Provider must capture the sent prompt."

    # 2. Verify original question appears in prompt
    assert question in prompt, f"Prompt must contain user question: '{question}'"

    # 3. Verify historical evidence fields appear in prompt
    assert "WELL_017" in prompt, "Prompt must contain well ID WELL_017"
    assert "Mud Loss" in prompt, "Prompt must contain event type Mud Loss"
    assert "High permeability" in prompt, "Prompt must contain cause High permeability"
    assert "WCR_017_001" in prompt, "Prompt must contain source report ID WCR_017_001"

    # 4. Verify prompt requires Historical Findings and Historical Inference
    assert "Historical Findings:" in prompt, "Prompt must require 'Historical Findings:' section"
    assert "Historical Inference:" in prompt, "Prompt must require 'Historical Inference:' section"

    # 5. Verify prompt specifies compact block format with expected fields
    assert "Well: <well_id>" in prompt or "Well:" in prompt, "Prompt must specify 'Well:' field"
    assert "Depth: <depth_m> m" in prompt or "Depth:" in prompt, "Prompt must specify 'Depth:' field"
    assert "Event: <event_type>" in prompt or "Event:" in prompt, "Prompt must specify 'Event:' field"
    assert "Cause: <cause>" in prompt or "Cause:" in prompt, "Prompt must specify 'Cause:' field"
    assert "Mitigation: <mitigation>" in prompt or "Mitigation:" in prompt, "Prompt must specify 'Mitigation:' field"
    assert "Outcome: <outcome>" in prompt or "Outcome:" in prompt, "Prompt must specify 'Outcome:' field"
    assert '---' in prompt, "Prompt must require '---' between records"

    # 6. Verify prompt forbids repetitive paragraphs, predictions, recommendations, and disclaimers
    assert "Do NOT turn the evidence into paragraphs" in prompt or "paragraphs" in prompt, (
        "Prompt must forbid turning evidence into paragraphs"
    )
    assert "Do NOT make future predictions" in prompt or "No Predictions" in prompt, (
        "Prompt must forbid future predictions"
    )
    assert "Do NOT provide recommended actions" in prompt or "No Recommendations" in prompt, (
        "Prompt must forbid recommendations"
    )
    assert "No Disclaimers" in prompt or "Do NOT add" in prompt, (
        "Prompt must forbid disclaimers"
    )
    assert "Important:" not in prompt, "Prompt must not require an 'Important' section"

    print("[PASSED] Test 1: Grounded answer generation with block format verification.\n")


def test_empty_intelligence_answer_generation():
    """
    Tests answer generation when no historical events match the query.
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
    empty_intelligence = {
        "historical_events": [],
        "pattern_analysis": {
            "total_events": 0,
            "unique_wells": 0,
            "most_common_event": None,
        },
        "evidence": [],
    }

    print("[TEST 2] Testing answer generation with empty intelligence payload:")
    answer = generator.generate_answer(question=question, historical_intelligence=empty_intelligence)

    assert answer == empty_canned_response
    prompt = provider.captured_prompt

    assert question in prompt
    assert "Historical Findings:" in prompt
    assert "Historical Inference:" in prompt
    assert "Important:" not in prompt

    print("[PASSED] Test 2: Empty intelligence handling verification.\n")


def main():
    print("=" * 50)
    print("RUNNING HISTORICAL ANSWER GENERATOR TESTS")
    print("=" * 50)
    test_standard_answer_generation()
    test_empty_intelligence_answer_generation()
    print("=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
