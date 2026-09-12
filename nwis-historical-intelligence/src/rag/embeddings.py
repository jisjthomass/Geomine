"""
Embedding provider abstraction and Gemini embedding integration for NWIS RAG pipeline.
Decouples embedding generation from document building and storage.
"""

from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv

# Module-level singleton client and cached API key to avoid re-constructing
# genai.Client across multiple requests
_gemini_client = None
_cached_api_key = None


def _get_gemini_client(api_key: str):
    """
    Lazily imports google.genai and constructs/reuses a genai.Client singleton.
    """
    global _gemini_client, _cached_api_key
    if _gemini_client is None or _cached_api_key != api_key:
        try:
            from google import genai
        except ImportError as e:
            raise ImportError(
                "google-genai package is not installed. "
                "Please install it with: pip install google-genai"
            ) from e
        _gemini_client = genai.Client(api_key=api_key)
        _cached_api_key = api_key
    return _gemini_client


class EmbeddingProvider(ABC):
    """
    Abstract base class for text embedding providers.
    Decouples document processing from specific embedding models/vendors.
    """

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string into a vector (list of floats).

        Args:
            text (str): The text content to embed.

        Returns:
            list[float]: Embedding vector.
        """
        pass


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Gemini Embedding Provider using the google-genai SDK.
    Follows project environment conventions, securely reading GEMINI_API_KEY
    and GEMINI_EMBEDDING_MODEL from environment without leaking secrets.
    """

    # Sensible default supported by Gemini API
    DEFAULT_MODEL = "gemini-embedding-001"

    def __init__(self, api_key: str = None, model: str = None):
        load_dotenv()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY env var."
            )
        self.model = model or os.environ.get("GEMINI_EMBEDDING_MODEL") or self.DEFAULT_MODEL
        self.client = _get_gemini_client(self.api_key)

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string into a vector using the Gemini embedding API.

        Args:
            text (str): The text content to embed.

        Returns:
            list[float]: The resulting embedding vector as a list of floats.

        Raises:
            TypeError: If input text is not a string.
            RuntimeError: If the Gemini API call fails or returns empty embeddings.
        """
        if not isinstance(text, str):
            raise TypeError(f"Expected text to be a string, got {type(text).__name__}")

        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
            )
            if not response or not response.embeddings:
                raise RuntimeError("Empty response received from Gemini embedding API.")

            embedding = response.embeddings[0].values
            if embedding is None:
                raise RuntimeError("No embedding values returned in response.")

            return [float(x) for x in embedding]
        except Exception as e:
            err_msg = str(e)
            if self.api_key and self.api_key in err_msg:
                err_msg = err_msg.replace(self.api_key, "[REDACTED]")
            raise RuntimeError(f"Gemini embedding generation failed: {err_msg}") from None


def embed_documents(documents: list[dict], provider: EmbeddingProvider) -> list[dict]:
    """
    Takes a list of document dictionaries (such as output from events_to_documents),
    generates embeddings using the specified EmbeddingProvider, and returns
    documents containing an additional 'embedding' field.

    Example input:
    [
        {
            "text": "Well: ...",
            "metadata": {...}
        }
    ]

    Example output:
    [
        {
            "text": "Well: ...",
            "metadata": {...},
            "embedding": [0.01, -0.02, ...]
        }
    ]

    Args:
        documents (list[dict]): List of document dicts with 'text' and 'metadata'.
        provider (EmbeddingProvider): An embedding provider instance.

    Returns:
        list[dict]: List of document dictionaries including 'embedding'.
    """
    if not documents:
        return []

    if provider is None or not hasattr(provider, "embed_text"):
        raise ValueError("A valid EmbeddingProvider instance with embed_text method is required.")

    embedded_docs = []
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        doc_copy = dict(doc)
        text = doc_copy.get("text", "")
        embedding = provider.embed_text(text)
        doc_copy["embedding"] = embedding
        embedded_docs.append(doc_copy)

    return embedded_docs
