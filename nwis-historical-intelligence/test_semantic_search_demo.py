"""
Manual integration and demonstration script for Stage 3 RAG semantic search.
Uses real historical data, real Gemini embeddings (gemini-embedding-001),
and InMemorySemanticIndex.

Usage:
    python nwis-historical-intelligence/test_semantic_search_demo.py [--limit 25] [--all]
"""

import argparse
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
from src.rag.document_builder import events_to_documents
from src.rag.embeddings import GeminiEmbeddingProvider, embed_documents
from src.rag.semantic_search import InMemorySemanticIndex


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
            import json
            with open(fallback_path, "r", encoding="utf-8") as f:
                events = json.load(f)

    return events


def print_results_table(query: str, results: list[dict]):
    """
    Print a clean result table containing ONLY:
    Query, Rank, Well, Depth, Formation, Event, Similarity.
    """
    print(f"Query: \"{query}\"")
    header = f"{'Rank':<5} | {'Well':<10} | {'Depth':<10} | {'Formation':<16} | {'Event':<24} | {'Similarity':<10}"
    separator = "-" * len(header)
    print(header)
    print(separator)
    for rank, res in enumerate(results, start=1):
        meta = res.get("metadata", {})
        well = str(meta.get("well_id", "N/A"))
        depth = f"{meta.get('depth_m', 'N/A')} m"
        formation = str(meta.get("formation", "N/A"))
        event = str(meta.get("event_type", "N/A"))
        sim = f"{res.get('similarity', 0.0):.4f}"
        print(f"{rank:<5} | {well:<10} | {depth:<10} | {formation:<16} | {event:<24} | {sim:<10}")
    print()


def run_demo(limit: int = 25):
    # Load environment variables
    dotenv_file = find_dotenv()
    if dotenv_file:
        load_dotenv(dotenv_file)
    else:
        load_dotenv()

    raw_events = load_events()
    if not raw_events:
        print("[ERROR] No historical events found to index.")
        return

    # Apply limit if requested
    if limit and limit > 0:
        events = raw_events[:limit]
    else:
        events = raw_events

    print(f"Loaded {len(events)} historical events")

    # 1. Convert events to document dicts
    documents = events_to_documents(events)

    # 2. Instantiate real Gemini embedding provider
    provider = GeminiEmbeddingProvider()

    # 3. Generate real Gemini embeddings
    embedded_docs = embed_documents(documents, provider)
    print(f"Generated embeddings for {len(embedded_docs)} documents")

    # 4. Build index and add documents
    index = InMemorySemanticIndex()
    index.add_documents(embedded_docs)
    print("Semantic search ready\n")

    # 5. Execute semantic queries
    queries = [
        "stuck pipe problem while drilling",
        "mud loss during drilling",
        "high torque while drilling",
    ]

    for query in queries:
        results = index.search(query=query, provider=provider, top_k=5)
        print_results_table(query, results)


def main():
    parser = argparse.ArgumentParser(description="Stage 3 RAG Semantic Search Demo")
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Number of historical events to embed for the demo (default: 25)",
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
