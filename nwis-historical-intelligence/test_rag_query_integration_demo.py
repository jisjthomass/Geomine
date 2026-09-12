"""
Manual integration demo for Stage 5 RAG query parsing and hybrid retrieval.
Coordinates existing query parsing with RAGRetrievalService and live Gemini embeddings.

Usage:
    python nwis-historical-intelligence/test_rag_query_integration_demo.py [--limit 60] [--all]
"""

import argparse
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

from dotenv import find_dotenv, load_dotenv
from src.llm import GeminiProvider, HistoricalQueryService, LLMQueryParser
from src.rag.embeddings import GeminiEmbeddingProvider
from src.rag.retrieval_service import RAGRetrievalService


def load_events():
    """
    Attempt to load real historical events via src.data_loader from PostgreSQL.
    If running outside Docker where PostgreSQL or psycopg2 is unavailable,
    fall back to nwis_mock_historical_events.json dataset.
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


def print_evidence(evidence_list: list[dict]):
    """
    Print ranked RAG evidence in clean, human-readable format.
    """
    if not evidence_list:
        print("No RAG evidence found.")
        return

    print("RAG Evidence:\n")
    for rank, ev in enumerate(evidence_list, start=1):
        meta = ev.get("metadata", {})
        well = meta.get("well_id", "N/A")
        depth = f"{meta.get('depth_m', 'N/A')} m"
        formation = meta.get("formation", "N/A")
        event = meta.get("event_type", "N/A")
        sem = f"{ev.get('semantic_similarity', 0.0):.4f}"
        struct = f"{ev.get('structured_score', 0.0):.4f}"
        hybrid = f"{ev.get('hybrid_score', 0.0):.4f}"

        print(f"{rank}. Well: {well}")
        print(f"   Depth: {depth}")
        print(f"   Formation: {formation}")
        print(f"   Event: {event}")
        print(f"   Semantic similarity: {sem}")
        print(f"   Structured score: {struct}")
        print(f"   Hybrid score: {hybrid}\n")


def run_demo(limit: int = 60):
    # Load environment variables (.env)
    dotenv_file = find_dotenv()
    if dotenv_file:
        load_dotenv(dotenv_file)
    else:
        load_dotenv()

    raw_events = load_events()
    if not raw_events:
        print("[ERROR] No historical events found.")
        return

    events = raw_events[:limit] if limit and limit > 0 else raw_events
    print(f"Loaded {len(events)} historical events")

    # 1. Initialize Gemini Embedding Provider and RAG Retrieval Service
    embedding_provider = GeminiEmbeddingProvider()
    rag_service = RAGRetrievalService(events=events, provider=embedding_provider)

    print("Preparing RAG retrieval service (generating document embeddings once)...")
    rag_service.prepare()
    print("RAG retrieval service prepared successfully.\n")

    # 2. Initialize Gemini LLM provider for query parsing
    llm_provider = GeminiProvider()
    query_parser = LLMQueryParser(llm_provider)
    query_service = HistoricalQueryService(
        provider=llm_provider,
        events=events,
        rag_service=rag_service,
    )

    # -------------------------------------------------------------
    # DEMO QUERY 1: Constrained Hybrid Query
    # -------------------------------------------------------------
    q1 = "What stuck pipe problems happened around 2800m in Formation X?"
    print("=" * 60)
    print("DEMO QUERY 1 (CONSTRAINED HYBRID SEARCH)")
    print("=" * 60)
    print(f"User Question: \"{q1}\"\n")

    nearby_wells = ["WELL_017", "WELL_021", "WELL_008"]
    response1 = query_service.answer_query(question=q1, nearby_well_ids=nearby_wells, top_k=5)

    print("Parsed query:")
    print(json.dumps(response1.get("parsed_query", {}), indent=2))
    print()

    print_evidence(response1.get("rag_evidence", []))

    # -------------------------------------------------------------
    # DEMO QUERY 2: General Semantic Query (No depth/formation required)
    # -------------------------------------------------------------
    q2 = "What drilling problems are associated with mud loss?"
    print("=" * 60)
    print("DEMO QUERY 2 (GENERAL SEMANTIC SEARCH)")
    print("=" * 60)
    print(f"User Question: \"{q2}\"\n")

    parsed_q2 = query_parser.parse(q2)
    print("Parsed query:")
    print(json.dumps(parsed_q2, indent=2))
    print()

    # Retrieve through RAG service with extracted parameters
    evidence_q2 = rag_service.retrieve(
        query=q2,
        current_depth=parsed_q2.get("current_depth"),
        formation=parsed_q2.get("formation"),
        depth_tolerance=parsed_q2.get("depth_tolerance", 100),
        event_type=parsed_q2.get("event_type"),
        top_k=5,
    )

    print_evidence(evidence_q2)


def main():
    parser = argparse.ArgumentParser(description="Stage 5 RAG Query Integration Demo")
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
