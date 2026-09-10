import os
from dotenv import load_dotenv
from .base import LLMProvider

# Module-level singleton: genai.Client is expensive to construct
# (sets up HTTP connection pool). Built once, reused every request.
_gemini_client = None
_gemini_config = None

def _get_client_and_config(api_key: str):
    global _gemini_client, _gemini_config
    if _gemini_client is None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ImportError(
                "google-genai package is not installed. "
                "Please install it with: pip install google-genai"
            ) from e
        _gemini_client = genai.Client(api_key=api_key)
        _gemini_config = types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            )
        )
    return _gemini_client, _gemini_config


class GeminiProvider(LLMProvider):
    """
    Gemini LLM Provider using google-genai SDK.
    Uses a module-level singleton client for maximum performance.
    """

    # gemini-2.0-flash-lite: fastest, cheapest production model
    DEFAULT_MODEL = "gemini-2.0-flash-lite"

    def __init__(self, api_key: str = None, model: str = None):
        load_dotenv()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY env var."
            )
        self.model = model or os.environ.get("GEMINI_MODEL") or self.DEFAULT_MODEL
        self.client, self._config = _get_client_and_config(self.api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._config,
        )
        return response.text if response and response.text else ""

    async def generate_async(self, prompt: str) -> str:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._config,
            )
            return response.text if response and response.text else ""
        except Exception as e:
            return f"Gemini API timeout or error: {e}"
