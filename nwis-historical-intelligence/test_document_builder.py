import os
import sys
import unittest

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.rag.document_builder import event_to_document, events_to_documents


def test_event_to_document():
    """
    Verify that event_to_document generates readable document text containing
    all key attributes from the synthetic event.
    """
    event = {
        "well_id": "TEST-001",
        "depth_m": 2800,
        "formation": "Formation X",
        "event_type": "Stuck Pipe",
        "cause": "Differential sticking",
        "mitigation": "Worked pipe",
        "outcome": "Pipe freed",
    }
    doc = event_to_document(event)

    print("[TEST 1] Testing event_to_document output:")
    print(doc)

    assert "TEST-001" in doc, "Expected 'TEST-001' in generated document"
    assert "2800" in doc, "Expected '2800' in generated document"
    assert "Formation X" in doc, "Expected 'Formation X' in generated document"
    assert "Stuck Pipe" in doc, "Expected 'Stuck Pipe' in generated document"
    assert "Differential sticking" in doc, "Expected 'Differential sticking' in generated document"
    assert "Worked pipe" in doc, "Expected 'Worked pipe' in generated document"
    assert "Pipe freed" in doc, "Expected 'Pipe freed' in generated document"
    print("[PASSED] test_event_to_document passed.\n")


def test_event_to_document_missing_fields():
    """
    Verify that event_to_document gracefully handles empty/missing fields
    without crashing.
    """
    empty_event = {}
    doc = event_to_document(empty_event)

    print("[TEST 2] Testing event_to_document with missing fields:")
    print(doc)

    assert isinstance(doc, str)
    assert "Well:" in doc
    assert "Depth:" in doc
    assert "Formation:" in doc
    assert "Event:" in doc
    assert "Cause:" in doc
    assert "Mitigation:" in doc
    assert "Outcome:" in doc
    print("[PASSED] test_event_to_document_missing_fields passed.\n")


def test_events_to_documents():
    """
    Verify that events_to_documents transforms an event list into a structured
    document list preserving text and metadata.
    """
    event = {
        "well_id": "TEST-001",
        "depth_m": 2800,
        "formation": "Formation X",
        "event_type": "Stuck Pipe",
        "cause": "Differential sticking",
        "mitigation": "Worked pipe",
        "outcome": "Pipe freed",
        "report_id": "RPT-001",
        "document_type": "WCR",
    }
    docs = events_to_documents([event])

    print("[TEST 3] Testing events_to_documents output:")
    print(docs)

    # 1. One input event produces one document
    assert len(docs) == 1, f"Expected 1 document, got {len(docs)}"

    # 2. Text exists
    assert "text" in docs[0], "Expected 'text' key in document"
    assert isinstance(docs[0]["text"], str) and len(docs[0]["text"]) > 0

    # 3. Metadata exists
    assert "metadata" in docs[0], "Expected 'metadata' key in document"
    metadata = docs[0]["metadata"]
    assert isinstance(metadata, dict)

    # 4. All metadata fields are preserved
    assert metadata.get("well_id") == "TEST-001", f"Expected 'TEST-001', got {metadata.get('well_id')}"
    assert metadata.get("depth_m") == 2800, f"Expected 2800, got {metadata.get('depth_m')}"
    assert metadata.get("formation") == "Formation X", f"Expected 'Formation X', got {metadata.get('formation')}"
    assert metadata.get("event_type") == "Stuck Pipe", f"Expected 'Stuck Pipe', got {metadata.get('event_type')}"
    assert metadata.get("cause") == "Differential sticking", f"Expected 'Differential sticking', got {metadata.get('cause')}"
    assert metadata.get("mitigation") == "Worked pipe", f"Expected 'Worked pipe', got {metadata.get('mitigation')}"
    assert metadata.get("outcome") == "Pipe freed", f"Expected 'Pipe freed', got {metadata.get('outcome')}"
    assert metadata.get("report_id") == "RPT-001", f"Expected 'RPT-001', got {metadata.get('report_id')}"
    assert metadata.get("document_type") == "WCR", f"Expected 'WCR', got {metadata.get('document_type')}"
    print("[PASSED] test_events_to_documents passed.\n")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest(unittest.FunctionTestCase(test_event_to_document))
    suite.addTest(unittest.FunctionTestCase(test_event_to_document_missing_fields))
    suite.addTest(unittest.FunctionTestCase(test_events_to_documents))
    return suite


def main():
    print("=" * 50)
    print("RUNNING DOCUMENT BUILDER TESTS")
    print("=" * 50)
    test_event_to_document()
    test_event_to_document_missing_fields()
    test_events_to_documents()
    print("=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
