"""LLM Layer package — client adapters, prompt caching, prompt-injection defense."""

from app.core.llm.base import LLMClient, hash_prompt
from app.core.llm.factory import clear_prompt_cache, get_llm_client
from app.core.llm.mock_client import MockLLMClient
from app.core.llm.prompts import render_prompt, sanitize_untrusted_input

__all__ = [
    "LLMClient",
    "MockLLMClient",
    "get_llm_client",
    "render_prompt",
    "sanitize_untrusted_input",
    "clear_prompt_cache",
    "hash_prompt",
]
