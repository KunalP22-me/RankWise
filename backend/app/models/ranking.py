from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.bias_report import BiasReport
    from app.models.candidate import Candidate
    from app.models.job import Job
    from app.models.override import Override


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RankingRun(Base):
    """A single ranking execution for a job. Stores status and overall results."""

    __tablename__ = "ranking_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending | running | completed | failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Config snapshot (weights used, blind mode, etc.)
    config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    job: Mapped[Job] = relationship("Job", back_populates="ranking_runs")
    candidate_rankings: Mapped[list[CandidateRanking]] = relationship(
        "CandidateRanking", back_populates="ranking_run", cascade="all, delete-orphan"
    )
    bias_report: Mapped[BiasReport | None] = relationship(
        "BiasReport", back_populates="ranking_run", uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RankingRun id={self.id!r} status={self.status!r}>"


class CandidateRanking(Base):
    """Per-candidate scoring result within a ranking run."""

    __tablename__ = "candidate_rankings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ranking_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ranking_runs.id", ondelete="CASCADE"), nullable=False
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Scores
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    must_have_score: Mapped[float] = mapped_column(Float, default=0.0)
    nice_to_have_score: Mapped[float] = mapped_column(Float, default=0.0)
    experience_fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    education_fit_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Override tracking
    overridden_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Per-requirement verdicts and scores (JSON array)
    requirement_scores: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Gap analysis (JSON: list of missing/weak requirements)
    gap_analysis: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # LLM-generated explanation (JSON: strengths, gaps, interview questions)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Supporting evidence snippets with offsets (JSON)
    evidence_snippets: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    ranking_run: Mapped[RankingRun] = relationship(
        "RankingRun", back_populates="candidate_rankings"
    )
    candidate: Mapped[Candidate] = relationship(
        "Candidate", back_populates="rankings"
    )
    overrides: Mapped[list[Override]] = relationship(
        "Override", back_populates="candidate_ranking", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CandidateRanking id={self.id!r} rank={self.rank} score={self.overall_score:.2f}>"


class RequirementScore(Base):
    """Detailed per-requirement score breakdown (optional granular table)."""

    __tablename__ = "requirement_scores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_ranking_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_rankings.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # must_have | nice_to_have

    # LLM verdict
    verdict: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Strong | Partial | None
    verdict_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Computed scores
    semantic_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_location_weight: Mapped[float] = mapped_column(Float, default=0.0)
    recency_weight: Mapped[float] = mapped_column(Float, default=0.0)
    duration_weight: Mapped[float] = mapped_column(Float, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Supporting snippet
    snippet_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    snippet_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snippet_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

