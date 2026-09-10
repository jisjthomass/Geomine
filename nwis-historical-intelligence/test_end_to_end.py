import json
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
from src.llm import GeminiProvider, HistoricalAnswerGenerator, HistoricalQueryService


def main():
    print("=" * 40)
    print("END-TO-END AI COPILOT TEST")
    print("=" * 40)

    # 1. Load historical events dataset
    dataset_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
    try:
        events = load_historical_events(dataset_path)
    except Exception as e:
        print(f"\n[ERROR] Failed to load dataset: {e}")
        return

    # 2. Initialize real Gemini provider and services
    try:
        provider = GeminiProvider()
        query_service = HistoricalQueryService(provider=provider, events=events)
        answer_generator = HistoricalAnswerGenerator(provider=provider)
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize Copilot services: {e}")
        return

    # 3. Define test question and nearby wells
    question = "What happened within 150 meters of 2800 m in Formation X?"
    nearby_wells = [
        "WELL_017",
        "WELL_021",
        "WELL_008",
    ]

    print("\nUSER QUESTION:")
    print(question)

    # 4. Execute query service (Question -> LLM Parser -> Deterministic Intelligence Engine)
    try:
        result = query_service.answer_query(question=question, nearby_well_ids=nearby_wells)
    except Exception as e:
        print(f"\n[ERROR] Error occurred during query processing / historical analysis: {e}")
        return

    parsed_query = result.get("parsed_query", {})
    historical_intelligence = result.get("historical_intelligence", {})
    historical_events = historical_intelligence.get("historical_events", [])
    pattern_analysis = historical_intelligence.get("pattern_analysis", {})
    evidence = historical_intelligence.get("evidence", [])

    print("\nPARSED QUERY:")
    print(json.dumps(parsed_query, indent=2))

    print("\nHISTORICAL EVENTS FOUND:")
    print(len(historical_events))

    print("\nPATTERN ANALYSIS:")
    print(json.dumps(pattern_analysis, indent=2))

    print("\nEVIDENCE:")
    print(json.dumps(evidence, indent=2))

    # 5. Generate final grounded natural language explanation using real Gemini LLM
    print("\n" + "-" * 40)
    print("FINAL AI ANSWER")
    print("-" * 40)
    try:
        final_answer = answer_generator.generate_answer(
            question=question,
            historical_intelligence=historical_intelligence,
        )
        print(final_answer)
    except Exception as e:
        print(f"[ERROR] Error occurred during answer generation: {e}")
    print("-" * 40)


if __name__ == "__main__":
    main()
