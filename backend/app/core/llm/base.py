"""Abstract base class and core contracts for LLM providers."""

import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("rankwise.llm")

T = TypeVar("T", bound=BaseModel)


def hash_prompt(prompt: str, model: str) -> str:
    """Generate deterministic SHA-256 hash for prompt and model."""
    key = f"{model}:{prompt}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def extract_json_from_text(text: str) -> dict:
    """Extract and parse JSON object from markdown code fences or raw string."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


class LLMClient(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate_text(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate raw text response from prompt."""
        pass

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float = 0.0,
        max_retries: int = 2,
    ) -> T:
        """Generate structured output validated against a Pydantic model with retry logic."""
        last_error: Exception | None = None
        current_prompt = prompt

        for attempt in range(max_retries + 1):
            try:
                raw_text = self.generate_text(current_prompt, temperature=temperature)
                data = extract_json_from_text(raw_text)
                return response_model.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(
                    f"LLM structured validation failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
                if attempt < max_retries:
                    # Provide feedback on validation error for self-correction
                    current_prompt = (
                        f"{prompt}\n\n"
                        f"IMPORTANT CORRECTION: Your previous output failed schema validation with error:\n"
                        f"{str(e)}\n"
                        f"Please output strictly valid JSON conforming exactly to the requested schema."
                    )

        raise ValueError(
            f"Failed to generate valid structured data for {response_model.__name__} "
            f"after {max_retries + 1} attempts. Error: {last_error}"
        )
