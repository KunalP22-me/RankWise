from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.ranking import RankingRun


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Job(Base):
    """A job posting with its description, parsed requirements, and scoring weights."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="draft"
    )  # draft | active | closed

    # LLM-parsed structured requirements (JSON)
    requirements_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Criterion weights (JSON dict: {"must_have": 0.4, "nice_to_have": 0.2, ...})
    weights: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=lambda: {
            "must_have": 0.40,
            "nice_to_have": 0.15,
            "experience_fit": 0.25,
            "education_fit": 0.20,
        }
    )

    # JD bias check results (JSON)
    bias_check_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Blind mode toggle
    blind_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    @property
    def requirements(self) -> dict | None:
        """Alias for requirements_json."""
        return self.requirements_json

    @requirements.setter
    def requirements(self, value: dict | None) -> None:
        self.requirements_json = value

    # Relationships
    candidates: Mapped[list[Candidate]] = relationship(
        "Candidate", back_populates="job", cascade="all, delete-orphan"
    )
    ranking_runs: Mapped[list[RankingRun]] = relationship(
        "RankingRun", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id!r} title={self.title!r}>"

