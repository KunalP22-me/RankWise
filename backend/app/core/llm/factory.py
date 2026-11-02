"""LLM Client Factory with response caching and audit logging."""

import logging
import time
from typing import TypeVar
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.llm.base import LLMClient, hash_prompt
from app.core.llm.claude_client import ClaudeClient
from app.core.llm.gemini_client import DEFAULT_GEMINI_MODEL, GeminiClient
from app.core.llm.mock_client import MockLLMClient
from app.core.llm.ollama_client import OllamaClient
from app.core.llm.openai_client import OpenAIClient
from app.models.audit_log import AuditLog

logger = logging.getLogger("rankwise.llm")

T = TypeVar("T", bound=BaseModel)

# In-memory prompt cache: key -> response text
_PROMPT_CACHE: dict[str, str] = {}


def clear_prompt_cache():
    """Clear in-memory prompt cache."""
    _PROMPT_CACHE.clear()


def get_cached_response(cache_key: str) -> str | None:
    """Retrieve response from cache if present."""
    return _PROMPT_CACHE.get(cache_key)


def set_cached_response(cache_key: str, response: str):
    """Store response in cache."""
    _PROMPT_CACHE[cache_key] = response


class CachedAuditedLLMClient(LLMClient):
    """Decorator around LLMClient providing transparent caching and audit logging."""

    def __init__(self, inner: LLMClient, provider: str, db: Session | None = None):
        super().__init__(model_name=inner.model_name)
        self.inner = inner
        self.provider = provider
        self.db = db

    def generate_text(self, prompt: str, temperature: float = 0.0) -> str:
        cache_key = hash_prompt(prompt, self.model_name)
        cached = get_cached_response(cache_key)
        if cached is not None:
            logger.debug(f"LLM cache hit for hash={cache_key[:8]}")
            return cached

        start_time = time.perf_counter()
        used_fallback = False
        try:
            response_text = self.inner.generate_text(prompt, temperature=temperature)
        except Exception as e:
            logger.error(
                f"Provider {self.provider} FAILED: {type(e).__name__}: {e}. "
                "Falling back to MockLLMClient (answer is NOT from a real LLM)."
            )
            used_fallback = True
            fallback = MockLLMClient()
            response_text = fallback.generate_text(prompt, temperature=temperature)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        if not used_fallback:  # never cache canned mock answers under the real model's key
            set_cached_response(cache_key, response_text)

        # Audit logging
        if self.db:
            try:
                log_entry = AuditLog(
                    action="llm_call",
                    user="system",
                    llm_provider=f"{self.provider}(FAILED->mock)" if used_fallback else self.provider,
                    llm_model=self.model_name,
                    prompt_hash=cache_key,
                    prompt_text=prompt[:1000],  # truncate long prompts for storage
                    response_text=response_text[:1000],
                    latency_ms=round(latency_ms, 2),
                    token_count=len(prompt.split()) + len(response_text.split()),
                )
                self.db.add(log_entry)
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to record LLM audit log: {e}")
                self.db.rollback()

        return response_text


def get_llm_client(
    provider: str | None = None,
    model: str | None = None,
    db: Session | None = None,
) -> LLMClient:
    """Factory function returning configured LLMClient wrapped with caching and audit logging."""
    prov = (provider or settings.llm_provider).lower()
    mod = model or settings.llm_model

    client: LLMClient
    if prov == "gemini":
        key = settings.gemini_api_key or settings.llm_api_key
        if not key:
            logger.warning("No Gemini API key found in config. Falling back to MockLLMClient.")
            client = MockLLMClient(model_name=mod or "mock-v1")
        else:
            client = GeminiClient(api_key=key, model_name=mod or DEFAULT_GEMINI_MODEL)

    elif prov == "openai":
        key = settings.openai_api_key or settings.llm_api_key
        if not key:
            logger.warning("No OpenAI API key found in config. Falling back to MockLLMClient.")
            client = MockLLMClient(model_name=mod or "mock-v1")
        else:
            client = OpenAIClient(api_key=key, model_name=mod or "gpt-4o-mini")

    elif prov == "claude":
        key = settings.anthropic_api_key or settings.llm_api_key
        if not key:
            logger.warning("No Anthropic API key found in config. Falling back to MockLLMClient.")
            client = MockLLMClient(model_name=mod or "mock-v1")
        else:
            client = ClaudeClient(api_key=key, model_name=mod or "claude-3-5-sonnet-20241022")

    elif prov == "ollama":
        client = OllamaClient(
            base_url=settings.llm_base_url,
            model_name=mod or "llama3:latest",
        )

    else:
        # Default: Mock provider
        client = MockLLMClient(model_name=mod or "mock-v1")

    return CachedAuditedLLMClient(inner=client, provider=prov, db=db)
