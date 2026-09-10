import json
import re
from .base import LLMProvider


class LLMQueryParser:
    """
    Translates natural language drilling queries into structured search parameters
    using an underlying LLMProvider without retrieving data or making ungrounded claims.
    """

    SYSTEM_PROMPT = """You are a drilling query parsing assistant.
Your sole job is to extract structured search parameters from a user's natural-language question about historical drilling events.

Extract the following fields:
1. current_depth: The drilling depth in meters (number or null).
2. formation: The geological formation name (string or null).
3. event_type: The specific drilling event/incident type if explicitly mentioned (string or null).
4. depth_tolerance: The depth tolerance window in meters if specified (number). If no tolerance is specified, default to 100.

Rules:
- Return ONLY a valid JSON object. No explanations, no markdown formatting outside of JSON.
- If a field cannot be determined from the query, set its value to null (except depth_tolerance which defaults to 100).
- Do not invent values or assume values that are not stated.

Examples:

Input: "What drilling problems happened around 2800 meters in Formation X?"
Output:
{
  "current_depth": 2800,
  "formation": "Formation X",
  "event_type": null,
  "depth_tolerance": 100
}

Input: "Show stuck pipe events near 2810m in Formation X within 50m."
Output:
{
  "current_depth": 2810,
  "formation": "Formation X",
  "event_type": "Stuck Pipe",
  "depth_tolerance": 50
}

Input: "What happened in Formation Y?"
Output:
{
  "current_depth": null,
  "formation": "Formation Y",
  "event_type": null,
  "depth_tolerance": 100
}
"""

    def __init__(self, provider: LLMProvider):
        """
        Initializes the LLMQueryParser with a given LLMProvider.

        Args:
            provider (LLMProvider): An instance of an LLM provider.
        """
        self.provider = provider

    def _clean_json_response(self, text: str) -> str:
        """
        Strips markdown code fences and extraneous leading/trailing whitespace.

        Args:
            text (str): Raw string from LLM output.

        Returns:
            str: Extracted JSON string.
        """
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    def parse(self, user_query: str) -> dict:
        """
        Parses a natural language query string into a structured dictionary of search parameters.

        Args:
            user_query (str): The natural language query from the user.

        Returns:
            dict: Structured search parameters with keys:
                  'current_depth', 'formation', 'event_type', 'depth_tolerance'.

        Raises:
            ValueError: If the response cannot be parsed as valid JSON or is missing required keys.
        """
        prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"Input: \"{user_query}\"\n"
            f"Output:"
        )

        raw_response = self.provider.generate(prompt)
        cleaned_json = self._clean_json_response(raw_response)

        try:
            parsed = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {raw_response}") from e

        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object, got: {type(parsed).__name__}")

        required_keys = {"current_depth", "formation", "event_type", "depth_tolerance"}
        missing_keys = required_keys - set(parsed.keys())
        if missing_keys:
            raise ValueError(f"LLM JSON response is missing required keys: {missing_keys}")

        depth_tolerance = parsed.get("depth_tolerance")
        if depth_tolerance is None:
            depth_tolerance = 100

        return {
            "current_depth": parsed.get("current_depth"),
            "formation": parsed.get("formation"),
            "event_type": parsed.get("event_type"),
            "depth_tolerance": depth_tolerance,
        }
