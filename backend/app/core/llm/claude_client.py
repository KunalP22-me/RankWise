"""Anthropic Claude LLM client adapter."""

import logging
from app.core.llm.base import LLMClient

logger = logging.getLogger("rankwise.llm")


class ClaudeClient(LLMClient):
    """Adapter for Anthropic Claude models."""

    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(model_name=model_name)
        self.api_key = api_key
        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=api_key)
        except ImportError:
            self._client = None
            logger.warning("anthropic package not installed.")

    def generate_text(self, prompt: str, temperature: float = 0.0) -> str:
        """Call Anthropic Messages API."""
        if not self._client:
            raise RuntimeError("Anthropic SDK not available.")
        message = self._client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text if message.content else ""
