from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ranking import RankingRun


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BiasReport(Base):
    """Bias analysis report generated for each ranking run."""

    __tablename__ = "bias_reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ranking_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ranking_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Adverse impact analysis (JSON: group rates, ratios, pass/fail)
    adverse_impact: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Counterfactual test results (JSON: deltas per candidate)
    counterfactual_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Proxy feature warnings (JSON: list of flagged correlations)
    proxy_warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Summary
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    flagged: Mapped[bool | None] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    ranking_run: Mapped[RankingRun] = relationship(
        "RankingRun", back_populates="bias_report"
    )

    def __repr__(self) -> str:
        return f"<BiasReport id={self.id!r} flagged={self.flagged}>"

