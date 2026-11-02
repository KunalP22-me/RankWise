"""Google Gemini LLM client adapter (uses the current google-genai SDK).

Works with the new "AQ." authentication keys from Google AI Studio as well as
older "AIza" keys. Includes automatic retry for free-tier rate limits (429) and
temporary server overload (503).
"""

import logging
import time

from app.core.llm.base import LLMClient

logger = logging.getLogger("rankwise.llm")

DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
_RETRY_DELAYS_SECONDS = (5, 15, 30)  # waits between attempts on rate limit / overload


def _is_retryable(error: Exception) -> bool:
    text = str(error).upper()
    return any(token in text for token in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "OVERLOADED"))


class GeminiClient(LLMClient):
    """Adapter for Google Gemini models via the google-genai package."""

    def __init__(self, api_key: str, model_name: str = DEFAULT_GEMINI_MODEL):
        super().__init__(model_name=model_name)
        self.api_key = api_key
        try:
            from google import genai
            from google.genai import types

            self._types = types
            self._client = genai.Client(api_key=api_key)
        except ImportError:
            self._client = None
            logger.warning("google-genai package not installed (pip install -U google-genai).")

    def generate_text(self, prompt: str, temperature: float = 0.0) -> str:
        """Call the Gemini API, retrying on rate limits."""
        if not self._client:
            raise RuntimeError("Gemini SDK not available. Run: pip install -U google-genai")

        last_error: Exception | None = None
        for attempt in range(len(_RETRY_DELAYS_SECONDS) + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self._types.GenerateContentConfig(temperature=temperature),
                )
                return response.text or ""
            except Exception as e:  # noqa: BLE001 - SDK raises several error types
                last_error = e
                if attempt < len(_RETRY_DELAYS_SECONDS) and _is_retryable(e):
                    delay = _RETRY_DELAYS_SECONDS[attempt]
                    logger.warning(f"Gemini busy/rate-limited ({e}). Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise
        raise last_error  # pragma: no cover
