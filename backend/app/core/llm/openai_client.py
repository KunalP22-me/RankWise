"""OpenAI LLM client adapter."""

import logging
from app.core.llm.base import LLMClient

logger = logging.getLogger("rankwise.llm")


class OpenAIClient(LLMClient):
    """Adapter for OpenAI models."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        super().__init__(model_name=model_name)
        self.api_key = api_key
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
        except ImportError:
            self._client = None
            logger.warning("openai package not installed.")

    def generate_text(self, prompt: str, temperature: float = 0.0) -> str:
        """Call OpenAI Chat Completions."""
        if not self._client:
            raise RuntimeError("OpenAI SDK not available.")
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
