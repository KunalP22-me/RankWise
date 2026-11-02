"""Audit log model — records every significant action and LLM call."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuditLog(Base):
    """Immutable audit log entry for actions, LLM calls, and changes."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # What happened
    action: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "llm_call", "override", "ranking_started", "upload"

    # Context
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    candidate_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user: Mapped[str] = mapped_column(String(200), default="system")

    # LLM call details (populated for action="llm_call")
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # General detail payload
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    @property
    def details(self) -> dict | None:
        return self.detail

    @details.setter
    def details(self, val: dict | None) -> None:
        self.detail = val

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id!r} action={self.action!r}>"
