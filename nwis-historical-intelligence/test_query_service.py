import os
import sys

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.data_loader import load_historical_events
from src.llm import LLMProvider, HistoricalQueryService


class MockProvider(LLMProvider):
    """
    Mock LLM provider returning preset JSON strings for test assertions.
    """
    def __init__(self, response_text: str):
        self.response_text = response_text

    def generate(self, prompt: str) -> str:
        return self.response_text


def test_successful_query_service():
    """
    Tests successful question parsing and execution of the deterministic
    historical intelligence engine.
    """
    dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
    events = load_historical_events(dataset_path)

    mock_response = (
        '{\n'
        '  "current_depth": 2800,\n'
        '  "formation": "Formation X",\n'
        '  "event_type": null,\n'
        '  "depth_tolerance": 100\n'
        '}'
    )
    provider = MockProvider(mock_response)
    service = HistoricalQueryService(provider=provider, events=events)

    question = "What drilling problems happened around 2800 meters in Formation X?"
    nearby_wells = ["WELL_017", "WELL_021", "WELL_008"]

    print("[TEST 1] Testing HistoricalQueryService with valid question:")
    print("Question:", question)
    print("Nearby wells:", nearby_wells)

    response = service.answer_query(question=question, nearby_well_ids=nearby_wells)

    # 1. Verify top-level structure
    assert "question" in response
    assert "parsed_query" in response
    assert "historical_intelligence" in response
    assert response["question"] == question

    # 2. Verify parsed query
    parsed = response["parsed_query"]
    assert parsed["current_depth"] == 2800
    assert parsed["formation"] == "Formation X"
    assert parsed["event_type"] is None
    assert parsed["depth_tolerance"] == 100

    # 3. Verify historical intelligence payload
    intel = response["historical_intelligence"]
    assert "historical_events" in intel
    assert "pattern_analysis" in intel
    assert "evidence" in intel

    # 4. Verify results content
    matching_events = intel["historical_events"]
    evidence_list = intel["evidence"]
    pattern = intel["pattern_analysis"]

    print(f"Total historical matches: {len(matching_events)}")
    print(f"Total evidence items: {len(evidence_list)}")
    print(f"Unique wells in pattern: {pattern.get('unique_wells')}")

    assert len(matching_events) > 0, "Expected at least one historical event!"
    assert len(evidence_list) == len(matching_events), "Evidence count must match event count!"
    assert pattern["total_events"] == len(matching_events)

    print("[PASSED] Test 1: Successful query and intelligence execution.\n")


def test_missing_depth_validation():
    """
    Tests that a question yielding null current_depth raises a clear ValueError.
    """
    dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
    events = load_historical_events(dataset_path)

    # Null depth response
    mock_response = (
        '{\n'
        '  "current_depth": null,\n'
        '  "formation": "Formation Y",\n'
        '  "event_type": null,\n'
        '  "depth_tolerance": 100\n'
        '}'
    )
    provider = MockProvider(mock_response)
    service = HistoricalQueryService(provider=provider, events=events)

    question = "What happened in Formation Y?"
    nearby_wells = ["WELL_001"]

    print("[TEST 2] Testing missing current_depth validation:")
    try:
        service.answer_query(question=question, nearby_well_ids=nearby_wells)
        assert False, "Expected ValueError was not raised for missing current_depth!"
    except ValueError as e:
        print(f"Caught expected ValueError: {e}")
        assert "drilling depth" in str(e)
        print("[PASSED] Test 2: Missing depth validation.\n")


def test_missing_formation_validation():
    """
    Tests that a question yielding null formation raises a clear ValueError.
    """
    dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
    events = load_historical_events(dataset_path)

    # Null formation response
    mock_response = (
        '{\n'
        '  "current_depth": 2500,\n'
        '  "formation": null,\n'
        '  "event_type": "Stuck Pipe",\n'
        '  "depth_tolerance": 100\n'
        '}'
    )
    provider = MockProvider(mock_response)
    service = HistoricalQueryService(provider=provider, events=events)

    question = "Show stuck pipe events around 2500 meters."
    nearby_wells = ["WELL_001"]

    print("[TEST 3] Testing missing formation validation:")
    try:
        service.answer_query(question=question, nearby_well_ids=nearby_wells)
        assert False, "Expected ValueError was not raised for missing formation!"
    except ValueError as e:
        print(f"Caught expected ValueError: {e}")
        assert "formation" in str(e)
        print("[PASSED] Test 3: Missing formation validation.\n")


def main():
    print("=" * 50)
    print("RUNNING HISTORICAL QUERY SERVICE TESTS")
    print("=" * 50)
    test_successful_query_service()
    test_missing_depth_validation()
    test_missing_formation_validation()
    print("=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
