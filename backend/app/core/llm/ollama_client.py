"""Local Ollama LLM client adapter via HTTP requests."""

import json
import logging
import urllib.request
import urllib.error
from app.core.llm.base import LLMClient

logger = logging.getLogger("rankwise.llm")


class OllamaClient(LLMClient):
    """Adapter for locally hosted Ollama models (e.g. llama3, mistral)."""

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3:latest"):
        super().__init__(model_name=model_name)
        self.base_url = base_url.rstrip("/")

    def generate_text(self, prompt: str, temperature: float = 0.0) -> str:
        """Call Ollama /api/generate endpoint."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_json = json.loads(resp.read().decode())
                return res_json.get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama connection failed at {url}: {e}") from e
