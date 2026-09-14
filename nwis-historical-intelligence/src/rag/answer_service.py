from typing import Any, Dict, List, Optional
from .context_builder import build_rag_context

try:
    from src.llm.answer_generator import HistoricalAnswerGenerator
except ImportError:
    from llm.answer_generator import HistoricalAnswerGenerator


class RAGAnswerService:
    """
    Coordinates retrieved historical evidence, context building, and
    grounded LLM answer generation.
    """

    def __init__(self, answer_generator: HistoricalAnswerGenerator, max_evidence: int = 5):
        """
        Initializes the RAGAnswerService.

        Args:
            answer_generator (HistoricalAnswerGenerator): The underlying answer generator instance.
            max_evidence (int): Maximum evidence items to format into grounding context. Defaults to 5.
        """
        self.answer_generator = answer_generator
        self.max_evidence = max_evidence

    def generate_answer(
        self,
        question: str,
        evidence: List[Dict[str, Any]],
        historical_intelligence: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Converts retrieved evidence into factual grounding context and generates
        a structured historical answer.

        Args:
            question (str): User natural-language question.
            evidence (list[dict]): Ranked historical evidence from HybridRetriever or RAGRetrievalService.
            historical_intelligence (dict, optional): Existing structured historical intelligence payload.

        Returns:
            str: Generated grounded answer adhering to Historical Findings and Historical Inference rules.
        """
        rag_context = build_rag_context(evidence, max_results=self.max_evidence)
        return self.answer_generator.generate_answer(
            question=question,
            historical_intelligence=historical_intelligence,
            rag_context=rag_context,
        )

    async def generate_answer_async(
        self,
        question: str,
        evidence: List[Dict[str, Any]],
        historical_intelligence: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Asynchronously converts retrieved evidence into factual grounding context
        and generates a structured historical answer.

        Args:
            question (str): User natural-language question.
            evidence (list[dict]): Ranked historical evidence from HybridRetriever or RAGRetrievalService.
            historical_intelligence (dict, optional): Existing structured historical intelligence payload.

        Returns:
            str: Generated grounded answer adhering to Historical Findings and Historical Inference rules.
        """
        rag_context = build_rag_context(evidence, max_results=self.max_evidence)
        return await self.answer_generator.generate_answer_async(
            question=question,
            historical_intelligence=historical_intelligence,
            rag_context=rag_context,
        )
