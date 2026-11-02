from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ranking import CandidateRanking


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Override(Base):
    """A recruiter override of a candidate's score, with categorized reason."""

    __tablename__ = "overrides"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_ranking_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidate_rankings.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Which score dimension was overridden (overall | must_have | nice_to_have | ...)
    criterion: Mapped[str] = mapped_column(String(100), default="overall")

    original_score: Mapped[float] = mapped_column(Float, nullable=False)
    new_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Categorized reason
    reason_category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "domain_expertise", "culture_fit", "incorrect_parsing", "other"
    reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit
    user: Mapped[str] = mapped_column(String(200), default="recruiter")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    candidate_ranking: Mapped[CandidateRanking] = relationship(
        "CandidateRanking", back_populates="overrides"
    )

    def __repr__(self) -> str:
        return (
            f"<Override id={self.id!r} criterion={self.criterion!r} "
            f"{self.original_score:.2f} -> {self.new_score:.2f}>"
        )

