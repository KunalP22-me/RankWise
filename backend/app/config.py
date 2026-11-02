"""RankWise application configuration via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──
    database_url: str = "sqlite:///./rankwise.db"

    # ── LLM ──
    llm_provider: str = "mock"  # gemini | openai | claude | ollama | mock
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str = "http://localhost:11434"

    # Provider-specific keys
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # ── App ──
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    parse_confidence_threshold: float = 0.6
    cors_origins: str = "http://localhost:5173"

    # ── Embedding Models ──
    bi_encoder_model: str = "all-MiniLM-L6-v2"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ── Bias ──
    counterfactual_delta_threshold: float = 0.05

    @property
    def upload_path(self) -> Path:
        """Resolved upload directory path."""
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
