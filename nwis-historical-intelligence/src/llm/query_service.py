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

    def __init__(self, provider: LLMProvider, events: list, rag_service=None, answer_generator=None):
        """
        Initializes the HistoricalQueryService.

        Args:
            provider (LLMProvider): An instance of an LLM provider for query parsing.
            events (list): Loaded historical drilling events dataset.
            rag_service (RAGRetrievalService, optional): Optional hybrid RAG retrieval service.
            answer_generator (HistoricalAnswerGenerator, optional): Optional answer generator for grounded responses.
        """
        self.provider = provider
        self.events = events
        self.parser = LLMQueryParser(provider)
        self.rag_service = rag_service
        self.answer_generator = answer_generator

    def answer_query(
        self,
        question: str,
        nearby_well_ids: list[str],
        top_k: int = 5,
        generate_answer: bool = False,
    ) -> dict:
        """
        Parses a natural language question and executes deterministic historical intelligence
        as well as hybrid RAG retrieval if a RAG service is attached. Optionally generates a
        grounded historical answer using the answer generator.

        Args:
            question (str): Natural language user question about drilling incidents.
            nearby_well_ids (list[str]): List of offset/nearby well IDs to search within.
            top_k (int): Number of top RAG evidence results to return.
            generate_answer (bool): Whether to generate a grounded natural language answer. Defaults to False.

        Returns:
            dict: A payload containing the original question, parsed parameters,
                  deterministic historical intelligence results, rag_evidence,
                  and optionally answer.

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

        # 4. Execute RAG retrieval if rag_service is available
        rag_evidence = []
        if self.rag_service is not None:
            try:
                rag_evidence = self.rag_service.retrieve(
                    query=question,
                    current_depth=current_depth,
                    formation=formation,
                    depth_tolerance=parsed_query.get("depth_tolerance", 100),
                    event_type=parsed_query.get("event_type"),
                    nearby_well_ids=nearby_well_ids,
                    top_k=top_k,
                )
            except Exception:
                rag_evidence = []

        # 5. Build response payload
        response = {
            "question": question,
            "parsed_query": parsed_query,
            "historical_intelligence": intelligence_result,
            "rag_evidence": rag_evidence,
        }

        # 6. Optionally generate grounded answer
        if generate_answer:
            generator = self.answer_generator
            if generator is None:
                try:
                    from .answer_generator import HistoricalAnswerGenerator
                except ImportError:
                    from answer_generator import HistoricalAnswerGenerator
                generator = HistoricalAnswerGenerator(self.provider)

            if rag_evidence:
                try:
                    from src.rag.context_builder import build_rag_context
                except ImportError:
                    from rag.context_builder import build_rag_context
                context = build_rag_context(rag_evidence, max_results=top_k)
            else:
                context = ""

            response["answer"] = generator.generate_answer(
                question=question,
                historical_intelligence=intelligence_result,
                rag_context=context,
            )

        return response
