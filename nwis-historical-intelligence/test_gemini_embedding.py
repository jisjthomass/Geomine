"""
Manual integration test for GeminiEmbeddingProvider against live Gemini API.

NOTE: This script is intended ONLY for explicit manual execution:
    python nwis-historical-intelligence/test_gemini_embedding.py
It is NOT part of automated unit tests and must not be run automatically.
"""

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
from src.rag.embeddings import GeminiEmbeddingProvider


def manual_gemini_embedding_test():
    # Load existing environment configuration (.env)
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()

    # Instantiate provider reusing existing environment/API conventions
    provider = GeminiEmbeddingProvider()

    # Embed one short test sentence
    test_sentence = "Differential sticking occurred at 2800m in Formation X."
    vector = provider.embed_text(test_sentence)

    # Print only the required output (do NOT print the vector or API key)
    print("embedding generated")
    print(f"vector dimension: {len(vector)}")


if __name__ == "__main__":
    manual_gemini_embedding_test()
