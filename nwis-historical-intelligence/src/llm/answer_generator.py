import json
from typing import Any, Dict, List, Optional

try:
    from .base import LLMProvider
except ImportError:
    from base import LLMProvider


class HistoricalAnswerGenerator:
    """
    Generates concise, engineer-focused explanations of historical drilling intelligence
    strictly grounded in verified offset well evidence and pattern analysis.
    """

    SYSTEM_INSTRUCTIONS = """You are an expert drilling intelligence assistant for offset well analysis.
Your job is to read the historical intelligence data (events, causes, mitigations) and provide a VERY CONCISE, single-paragraph summary of the historical hazards and how they were solved.

CRITICAL RULES:
1. Be extremely concise. Maximum 3-4 sentences.
2. Focus ONLY on the most dominant patterns (e.g. "Historically, 16 offset wells experienced Stuck Pipe due to differential sticking, which was successfully mitigated using pipe laxative pills.").
3. DO NOT list individual wells. DO NOT list individual depths. 
4. DO NOT use markdown headers or bullet points. Output plain text only.
5. Tone: Professional, concise, engineering-focused.
"""

    RAG_SYSTEM_INSTRUCTIONS = """ROLE:
You are an assistant for historical drilling-event analysis.

GROUNDING RULES:
1. Use ONLY the supplied historical evidence to make factual claims about events.
2. You may summarize or combine information explicitly supported by the evidence.
3. Do NOT invent wells, depths, formations, events, causes, mitigations, outcomes, or report IDs.
4. Do NOT make future predictions or claim that a historical event will happen again.
5. Do NOT provide operational recommendations or recommended actions.
6. Do NOT discuss ML risk prediction.
7. Do NOT turn the evidence into paragraphs or narrative prose in Historical Findings.
8. Do NOT use information that was not supplied in the retrieved evidence.
9. No Disclaimers. Do NOT add disclaimers, apologies, or conversational filler.

OUTPUT FORMAT REQUIREMENTS:
The answer MUST distinguish between Historical Findings and Historical Inference, and MUST use this exact structure:

Historical Findings:

Well: <well>
Depth: <depth> m
Event: <event>
Cause: <cause>
Mitigation: <mitigation>
Outcome: <outcome>

---

Well: <well>
Depth: <depth> m
Event: <event>
Cause: <cause>
Mitigation: <mitigation>
Outcome: <outcome>

---

Historical Inference:

<natural-language inference based only on the historical evidence>

FORMAT RULES:
- One evidence block per retrieved event.
- Use exactly the fields above: Well, Depth, Event, Cause, Mitigation, Outcome.
- Separate evidence blocks with '---'.
- There must be no introductory paragraph before Historical Findings.
- Historical Inference must be the final section.
- If a field is missing, use "Not recorded" rather than inventing a value.
- Do not include similarity scores in the final answer.
- Do not include JSON.
- Do not include Markdown tables.
- Do not include recommendations.
- Do not include future predictions.
"""

    def __init__(self, provider: LLMProvider):
        """
        Initializes the HistoricalAnswerGenerator.

        Args:
            provider (LLMProvider): An instance of an LLM provider.
        """
        self.provider = provider

    def generate_answer(
        self,
        question: str,
        historical_intelligence: Optional[Dict[str, Any]] = None,
        rag_context: Optional[str] = None,
        rag_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Builds a grounded prompt and invokes the LLM provider to explain the historical intelligence
        or explain retrieved RAG evidence.

        Args:
            question (str): The user's original natural language question.
            historical_intelligence (dict, optional): Deterministic payload containing:
                - 'historical_events': list of matching event dicts.
                - 'pattern_analysis': aggregated metrics dict.
                - 'evidence': list of deterministic evidence dicts.
            rag_context (str, optional): Formatted historical RAG evidence text context.
            rag_evidence (list[dict], optional): Raw or ranked RAG evidence items.

        Returns:
            str: Generated natural language explanation.
        """
        if rag_evidence is not None and rag_context is None:
            try:
                from src.rag.context_builder import build_rag_context
            except ImportError:
                from rag.context_builder import build_rag_context
            rag_context = build_rag_context(rag_evidence)

        if rag_context is not None:
            context_body = rag_context.strip() if rag_context.strip() else "No matching historical records found."
            prompt = (
                f"{self.RAG_SYSTEM_INSTRUCTIONS}\n\n"
                f"=== RETRIEVED HISTORICAL EVIDENCE (GROUND TRUTH) ===\n"
                f"{context_body}\n\n"
                f"=== USER QUESTION ===\n"
                f"{question}\n\n"
                f"=== YOUR GROUNDED ANSWER ==="
            )
            return self.provider.generate(prompt)

        formatted_intel = json.dumps(historical_intelligence, indent=2) if historical_intelligence is not None else "{}"

        prompt = (
            f"{self.SYSTEM_INSTRUCTIONS}\n\n"
            f"=== USER QUESTION ===\n"
            f"{question}\n\n"
            f"=== HISTORICAL INTELLIGENCE DATA (SOURCE OF TRUTH) ===\n"
            f"{formatted_intel}\n\n"
            f"=== YOUR GROUNDED EXPLANATION ==="
        )

        return self.provider.generate(prompt)

    async def generate_answer_async(
        self,
        question: str,
        historical_intelligence: Optional[Dict[str, Any]] = None,
        rag_context: Optional[str] = None,
        rag_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Asynchronously builds a grounded prompt and invokes the LLM provider.
        """
        if rag_evidence is not None and rag_context is None:
            try:
                from src.rag.context_builder import build_rag_context
            except ImportError:
                from rag.context_builder import build_rag_context
            rag_context = build_rag_context(rag_evidence)

        if rag_context is not None:
            context_body = rag_context.strip() if rag_context.strip() else "No matching historical records found."
            prompt = (
                f"{self.RAG_SYSTEM_INSTRUCTIONS}\n\n"
                f"=== RETRIEVED HISTORICAL EVIDENCE (GROUND TRUTH) ===\n"
                f"{context_body}\n\n"
                f"=== USER QUESTION ===\n"
                f"{question}\n\n"
                f"=== YOUR GROUNDED ANSWER ==="
            )
        else:
            formatted_intel = json.dumps(historical_intelligence, indent=2) if historical_intelligence is not None else "{}"
            prompt = (
                f"{self.SYSTEM_INSTRUCTIONS}\n\n"
                f"=== USER QUESTION ===\n"
                f"{question}\n\n"
                f"=== HISTORICAL INTELLIGENCE DATA (SOURCE OF TRUTH) ===\n"
                f"{formatted_intel}\n\n"
                f"=== YOUR GROUNDED EXPLANATION ==="
            )

        if hasattr(self.provider, 'generate_async'):
            return await self.provider.generate_async(prompt)
        return self.provider.generate(prompt)
