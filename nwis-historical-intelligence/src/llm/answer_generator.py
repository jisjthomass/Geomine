import json
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

    def __init__(self, provider: LLMProvider):
        """
        Initializes the HistoricalAnswerGenerator.

        Args:
            provider (LLMProvider): An instance of an LLM provider.
        """
        self.provider = provider

    def generate_answer(self, question: str, historical_intelligence: dict) -> str:
        """
        Builds a grounded prompt and invokes the LLM provider to explain the historical intelligence.

        Args:
            question (str): The user's original natural language question.
            historical_intelligence (dict): Deterministic payload containing:
                - 'historical_events': list of matching event dicts.
                - 'pattern_analysis': aggregated metrics dict.
                - 'evidence': list of deterministic evidence dicts.

        Returns:
            str: Generated natural language explanation.
        """
        formatted_intel = json.dumps(historical_intelligence, indent=2)

        prompt = (
            f"{self.SYSTEM_INSTRUCTIONS}\n\n"
            f"=== USER QUESTION ===\n"
            f"{question}\n\n"
            f"=== HISTORICAL INTELLIGENCE DATA (SOURCE OF TRUTH) ===\n"
            f"{formatted_intel}\n\n"
            f"=== YOUR GROUNDED EXPLANATION ==="
        )

        return self.provider.generate(prompt)

    async def generate_answer_async(self, question: str, historical_intelligence: dict) -> str:
        formatted_intel = json.dumps(historical_intelligence, indent=2)

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
