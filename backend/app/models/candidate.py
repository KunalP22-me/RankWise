from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.ranking import CandidateRanking


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Candidate(Base):
    """A candidate who has applied to a job, with parsed resume data."""

    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )

    # File info
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf | docx

    # Raw extracted text
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured parsed data (JSON matching ResumeData schema)
    parsed_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Parsing metadata
    parse_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # rules | llm | hybrid
    parse_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    parse_warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Computed fields
    total_experience_years: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Embedding cache key
    embedding_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="uploaded"
    )  # uploaded | parsed | ranked | shortlisted | rejected

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    job: Mapped[Job] = relationship("Job", back_populates="candidates")
    rankings: Mapped[list[CandidateRanking]] = relationship(
        "CandidateRanking", back_populates="candidate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id!r} filename={self.filename!r}>"

