from .base import LLMProvider
from .query_parser import LLMQueryParser

try:
    from src.intelligence import analyze_well
except ImportError:
    from intelligence import analyze_well


class HistoricalQueryService:
    """
    Coordinates natural-language query understanding with the deterministic
    historical intelligence engine.
    """

    def __init__(self, provider: LLMProvider, events: list):
        """
        Initializes the HistoricalQueryService.

        Args:
            provider (LLMProvider): An instance of an LLM provider for query parsing.
            events (list): Loaded historical drilling events dataset.
        """
        self.provider = provider
        self.events = events
        self.parser = LLMQueryParser(provider)

    def answer_query(self, question: str, nearby_well_ids: list[str]) -> dict:
        """
        Parses a natural language question and executes deterministic historical intelligence.

        Args:
            question (str): Natural language user question about drilling incidents.
            nearby_well_ids (list[str]): List of offset/nearby well IDs to search within.

        Returns:
            dict: A payload containing the original question, parsed parameters,
                  and deterministic historical intelligence results.

        Raises:
            ValueError: If current_depth or formation cannot be extracted from the question.
        """
        # 1. Parse question into structured parameters
        parsed_query = self.parser.parse(question)

        # 2. Validate essential parameters
        current_depth = parsed_query.get("current_depth")
        formation = parsed_query.get("formation")

        if current_depth is None or formation is None:
            missing = []
            if current_depth is None:
                missing.append("drilling depth (current_depth)")
            if formation is None:
                missing.append("geological formation (formation)")
            raise ValueError(
                f"Cannot execute historical intelligence search. "
                f"Missing required search parameter(s): {', '.join(missing)}. "
                f"Please specify both the drilling depth and formation in your question."
            )

        # 3. Execute deterministic historical intelligence pipeline
        intelligence_result = analyze_well(
            events=self.events,
            nearby_well_ids=nearby_well_ids,
            current_depth=current_depth,
            formation=formation,
            event_type=parsed_query.get("event_type"),
            depth_tolerance=parsed_query.get("depth_tolerance", 100),
        )

        # 4. Return combined response payload
        return {
            "question": question,
            "parsed_query": parsed_query,
            "historical_intelligence": intelligence_result,
        }
