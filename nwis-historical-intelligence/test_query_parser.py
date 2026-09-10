import os
import sys

# Ensure project root and src are on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.llm import LLMProvider, LLMQueryParser


class MockProvider(LLMProvider):
    """
    Mock LLM provider returning predetermined string responses for testing.
    """
    def __init__(self, response_text: str = None):
        self.response_text = response_text or (
            '{\n'
            '  "current_depth": 2800,\n'
            '  "formation": "Formation X",\n'
            '  "event_type": null,\n'
            '  "depth_tolerance": 100\n'
            '}'
        )

    def generate(self, prompt: str) -> str:
        return self.response_text


def test_standard_query_parsing():
    """Test standard JSON parsing without markdown fences."""
    mock_provider = MockProvider(
        '{"current_depth": 2800, "formation": "Formation X", "event_type": null, "depth_tolerance": 100}'
    )
    parser = LLMQueryParser(mock_provider)
    result = parser.parse("What drilling problems happened around 2800 meters in Formation X?")

    print("[TEST 1] Standard JSON parsing test:")
    print("Parsed output:", result)

    assert result["current_depth"] == 2800, f"Expected 2800, got {result['current_depth']}"
    assert result["formation"] == "Formation X", f"Expected 'Formation X', got {result['formation']}"
    assert result["event_type"] is None, f"Expected None, got {result['event_type']}"
    assert result["depth_tolerance"] == 100, f"Expected 100, got {result['depth_tolerance']}"
    print("[PASSED] Test 1 Passed.\n")


def test_markdown_fence_handling():
    """Test handling of markdown code blocks (```json ... ``` and ``` ... ```)."""
    # 1. With ```json
    mock_json_block = (
        "```json\n"
        "{\n"
        '  "current_depth": 2810,\n'
        '  "formation": "Formation X",\n'
        '  "event_type": "Stuck Pipe",\n'
        '  "depth_tolerance": 50\n'
        "}\n"
        "```"
    )
    parser1 = LLMQueryParser(MockProvider(mock_json_block))
    result1 = parser1.parse("Show stuck pipe events near 2810m in Formation X within 50m.")

    print("[TEST 2A] Markdown fence with 'json' tag:")
    print("Parsed output:", result1)
    assert result1["current_depth"] == 2810
    assert result1["formation"] == "Formation X"
    assert result1["event_type"] == "Stuck Pipe"
    assert result1["depth_tolerance"] == 50
    print("[PASSED] Test 2A Passed.\n")

    # 2. With plain ```
    mock_plain_block = (
        "```\n"
        "{\n"
        '  "current_depth": null,\n'
        '  "formation": "Formation Y",\n'
        '  "event_type": null,\n'
        '  "depth_tolerance": 100\n'
        "}\n"
        "```"
    )
    parser2 = LLMQueryParser(MockProvider(mock_plain_block))
    result2 = parser2.parse("What happened in Formation Y?")

    print("[TEST 2B] Markdown fence without language tag:")
    print("Parsed output:", result2)
    assert result2["current_depth"] is None
    assert result2["formation"] == "Formation Y"
    assert result2["event_type"] is None
    assert result2["depth_tolerance"] == 100
    print("[PASSED] Test 2B Passed.\n")


def test_invalid_json_handling():
    """Test that malformed responses raise a descriptive ValueError."""
    parser = LLMQueryParser(MockProvider("This is not valid JSON at all"))
    print("[TEST 3] Invalid JSON error handling:")
    try:
        parser.parse("Test query")
        assert False, "Expected ValueError was not raised!"
    except ValueError as e:
        print(f"Caught expected ValueError: {e}")
        print("[PASSED] Test 3 Passed.\n")


def test_missing_keys_handling():
    """Test that missing required keys raise a ValueError."""
    parser = LLMQueryParser(MockProvider('{"formation": "Formation X"}'))
    print("[TEST 4] Missing keys error handling:")
    try:
        parser.parse("Test query")
        assert False, "Expected ValueError was not raised!"
    except ValueError as e:
        print(f"Caught expected ValueError: {e}")
        print("[PASSED] Test 4 Passed.\n")



def main():
    print("=" * 50)
    print("RUNNING LLM QUERY PARSER TESTS")
    print("=" * 50)
    test_standard_query_parsing()
    test_markdown_fence_handling()
    test_invalid_json_handling()
    test_missing_keys_handling()
    print("=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    main()
