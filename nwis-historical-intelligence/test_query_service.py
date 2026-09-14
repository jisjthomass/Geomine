import os
import sys

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from src.data_loader import load_historical_events
except ImportError:
    import json
    def load_historical_events(file_path=None):
        path = file_path or os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

from src.llm import LLMProvider, HistoricalQueryService
from src.rag.embeddings import EmbeddingProvider
from src.rag.retrieval_service import RAGRetrievalService


class MockProvider(LLMProvider):
    """
    Mock LLM provider returning preset JSON strings for test assertions.
    """
    def __init__(self, response_text: str):
        self.response_text = response_text

    def generate(self, prompt: str) -> str:
        return self.response_text


class MockFakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic fake embedding provider for testing RAG service with QueryService."""
    def embed_text(self, text: str) -> list[float]:
        return [0.7, 0.7, 0.0]


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
    assert "rag_evidence" in response
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


def test_query_service_with_rag_evidence():
    """
    Tests that HistoricalQueryService coordinates with RAGRetrievalService
    to return rag_evidence alongside historical_intelligence without breaking.
    """
    dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
    events = load_historical_events(dataset_path)

    mock_response = (
        '{\n'
        '  "current_depth": 2800,\n'
        '  "formation": "Formation X",\n'
        '  "event_type": "Stuck Pipe",\n'
        '  "depth_tolerance": 100\n'
        '}'
    )
    llm_provider = MockProvider(mock_response)
    embedding_provider = MockFakeEmbeddingProvider()
    rag_service = RAGRetrievalService(events=events[:20], provider=embedding_provider, auto_prepare=True)

    service = HistoricalQueryService(provider=llm_provider, events=events, rag_service=rag_service)

    question = "What stuck pipe problems happened around 2800 meters in Formation X?"
    nearby_wells = ["WELL_017", "WELL_021", "WELL_008"]

    print("[TEST 4] Testing HistoricalQueryService with attached RAGRetrievalService:")
    response = service.answer_query(question=question, nearby_well_ids=nearby_wells, top_k=3)

    # Verify both historical_intelligence and rag_evidence are populated
    assert "historical_intelligence" in response
    assert len(response["historical_intelligence"]["historical_events"]) > 0

    assert "rag_evidence" in response
    assert len(response["rag_evidence"]) == 3
    for ev in response["rag_evidence"]:
        assert "text" in ev
        assert "metadata" in ev
        assert "hybrid_score" in ev
        assert "semantic_similarity" in ev
        assert "structured_score" in ev

    print(f"RAG evidence items returned: {len(response['rag_evidence'])}")
    print("[PASSED] Test 4: QueryService with RAG retrieval successfully executed.\n")


def test_query_service_optional_answer_generation():
    """
    Tests that HistoricalQueryService supports generate_answer=True to produce
    grounded answers while keeping historical_intelligence and rag_evidence intact,
    and defaults to generate_answer=False without extra overhead.
    """
    dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
    events = load_historical_events(dataset_path)

    parse_json = (
        '{\n'
        '  "current_depth": 2800,\n'
        '  "formation": "Formation X",\n'
        '  "event_type": "Stuck Pipe",\n'
        '  "depth_tolerance": 100\n'
        '}'
    )

    class MultiCallProvider(LLMProvider):
        def generate(self, prompt: str) -> str:
            if "Extract the structured parameters" in prompt or "{" in prompt:
                return parse_json
            return (
                "Historical Findings:\n\n"
                "Well: WELL_017\nDepth: 2780 m\nEvent: Mud Loss\nCause: High permeability\n"
                "Mitigation: Increased mud weight\nOutcome: Losses controlled\n\n---\n\n"
                "Historical Inference:\nPermeability-driven loss observed."
            )

    provider = MultiCallProvider()
    embedding_provider = MockFakeEmbeddingProvider()
    rag_service = RAGRetrievalService(events=events[:20], provider=embedding_provider, auto_prepare=True)
    service = HistoricalQueryService(provider=provider, events=events, rag_service=rag_service)

    question = "What stuck pipe problems happened around 2800 meters in Formation X?"
    nearby_wells = ["WELL_017", "WELL_021", "WELL_008"]

    print("[TEST 5] Testing HistoricalQueryService with generate_answer=False (default):")
    res_default = service.answer_query(question=question, nearby_well_ids=nearby_wells)
    assert "answer" not in res_default, "Default generate_answer=False must not add 'answer' field"
    assert "historical_intelligence" in res_default
    assert "rag_evidence" in res_default
    print("[PASSED] Default generate_answer=False verified.\n")

    print("[TEST 6] Testing HistoricalQueryService with generate_answer=True:")
    res_with_answer = service.answer_query(question=question, nearby_well_ids=nearby_wells, generate_answer=True)
    assert "answer" in res_with_answer, "generate_answer=True must populate 'answer' field"
    assert "Historical Findings:" in res_with_answer["answer"]
    assert "Historical Inference:" in res_with_answer["answer"]
    assert "historical_intelligence" in res_with_answer
    assert "rag_evidence" in res_with_answer
    print("[PASSED] generate_answer=True successfully returned grounded answer.\n")


def main():
    print("=" * 50)
    print("RUNNING HISTORICAL QUERY SERVICE TESTS")
    print("=" * 50)
    test_successful_query_service()
    test_missing_depth_validation()
    test_missing_formation_validation()
    test_query_service_with_rag_evidence()
    test_query_service_optional_answer_generation()
    print("=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()

