import argparse
import json
import os
import sys
from dotenv import find_dotenv, load_dotenv

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Load environment variables (.env contains GEMINI_API_KEY)
dotenv_file = find_dotenv()
if dotenv_file:
    load_dotenv(dotenv_file)
else:
    load_dotenv()

from src.rag import (
    GeminiEmbeddingProvider,
    RAGRetrievalService,
    compute_structured_score,
)
from src.llm import GeminiProvider, HistoricalQueryService


def load_events():
    """
    Attempt to load real historical events via src.data_loader from PostgreSQL.
    If running outside Docker or without PostgreSQL, fall back to mock dataset.
    """
    events = []
    try:
        from src.data_loader import load_historical_events
        events = load_historical_events()
    except ImportError as e:
        print(f"[Notice] psycopg2 not available on host ({e}).")
    except Exception as e:
        print(f"[Notice] Could not load directly from PostgreSQL: {e}")

    if not events:
        fallback_path = os.path.join(PROJECT_ROOT, "nwis_mock_historical_events.json")
        if os.path.exists(fallback_path):
            print("[Notice] Using local historical dataset fallback (nwis_mock_historical_events.json).")
            with open(fallback_path, "r", encoding="utf-8") as f:
                events = json.load(f)

    return events


def run_demo(limit: int = 60, nearby_wells: list = None):
    # 1. Load historical events dataset
    raw_events = load_events()
    if not raw_events:
        print("[ERROR] No historical events found.")
        return

    events = raw_events[:limit] if limit and limit > 0 else raw_events
    print(f"Loaded {len(events)} historical events for indexing.\n")

    # 2. Initialize real Gemini embedding provider and RAG retrieval service
    embedding_provider = GeminiEmbeddingProvider()
    rag_service = RAGRetrievalService(
        events=events,
        provider=embedding_provider,
        auto_prepare=True,
    )

    # 3. Initialize real Gemini LLM provider and query service
    gemini_provider = GeminiProvider()
    query_service = HistoricalQueryService(
        provider=gemini_provider,
        events=events,
        rag_service=rag_service,
    )

    # 4. User question & optional offset well context from caller/GIS
    question = "What stuck pipe problems happened around 2800m in Formation X?"
    if nearby_wells is None:
        nearby_wells = ["WELL_017", "WELL_021", "WELL_008"]

    print("=" * 70)
    print("STAGE 6 LIVE RAG INTEGRATION DEMO")
    print("=" * 70)
    print(f"Question: \"{question}\"\n")

    # 5. Execute full query pipeline (Parse -> Retrieve -> Build Context -> Grounded Answer)
    response = query_service.answer_query(
        question=question,
        nearby_well_ids=nearby_wells,
        top_k=5,
        generate_answer=True,
    )

    parsed_q = response.get("parsed_query", {})
    evidence = response.get("rag_evidence", [])
    answer = response.get("answer", "")

    # Calculate structured candidate count dynamically
    structured_candidates = [
        e for e in events
        if compute_structured_score(
            metadata=e,
            formation=parsed_q.get("formation"),
            current_depth=parsed_q.get("current_depth"),
            depth_tolerance=parsed_q.get("depth_tolerance", 100),
            event_type=parsed_q.get("event_type"),
            nearby_well_ids=nearby_wells,
        ) > 0.0
    ]

    # 6. Print Diagnostic Summary
    print("-" * 70)
    print("DIAGNOSTIC RETRIEVAL SUMMARY")
    print("-" * 70)
    print("Parsed Query:")
    print(json.dumps(parsed_q, indent=2))
    print(f"\nDataset Size: {len(events)} records")
    print(f"Structured Candidate Count: {len(structured_candidates)} records (score > 0.0)")
    print(f"Retrieved Result Count: {len(evidence)} records")

    print("\nTop Retrieved Records:")
    for idx, item in enumerate(evidence, start=1):
        meta = item.get("metadata", {})
        well = meta.get("well_id", "Unknown")
        depth = meta.get("depth_m", "Unknown")
        form = meta.get("formation", "Unknown")
        evt = meta.get("event_type", "Unknown")
        sem = f"{item.get('semantic_similarity', 0.0):.4f}"
        struct = f"{item.get('structured_score', 0.0):.4f}"
        hybrid = f"{item.get('hybrid_score', 0.0):.4f}"
        print(f"  {idx}. Well: {well:<10} | Depth: {depth:>4} m | Formation: {form:<12} | Event: {evt:<22} | "
              f"Semantic: {sem} | Structured: {struct} | Hybrid: {hybrid}")

    print("\n" + "=" * 70)
    print("GENERATED GROUNDED ANSWER")
    print("=" * 70)
    print(answer)
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Stage 6 RAG Answer Generation Live Demo")
    parser.add_argument(
        "--limit",
        type=int,
        default=60,
        help="Number of historical events to embed for the demo (default: 60)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Embed all available historical events",
    )
    args = parser.parse_args()

    limit = None if args.all else args.limit
    run_demo(limit=limit)


if __name__ == "__main__":
    main()
