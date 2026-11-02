"""Pydantic v2 schemas for rankings and scoring results."""

from datetime import datetime

from pydantic import BaseModel, Field


class RequirementScoreResponse(BaseModel):
    """Score breakdown for a single requirement."""
    requirement_text: str
    requirement_type: str
    verdict: str  # Strong | Partial | None
    verdict_reason: str | None = None
    semantic_similarity: float = 0.0
    final_score: float = 0.0
    snippet_text: str | None = None
    snippet_start: int | None = None
    snippet_end: int | None = None


class ExplanationResponse(BaseModel):
    """LLM-generated candidate explanation."""
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    summary: str = ""


class CandidateRankingResponse(BaseModel):
    """Per-candidate ranking result."""
    id: str
    candidate_id: str
    rank: int | None = None
    overall_score: float
    must_have_score: float
    nice_to_have_score: float
    experience_fit_score: float
    education_fit_score: float
    overridden_score: float | None = None
    requirement_scores: list | None = None
    gap_analysis: list | None = None
    explanation: dict | None = None
    evidence_snippets: list | None = None
    created_at: datetime

    # Joined candidate info
    candidate_name: str | None = None
    candidate_filename: str | None = None

    model_config = {"from_attributes": True}


class RankingRunResponse(BaseModel):
    """Response for a ranking run."""
    id: str
    job_id: str
    status: str
    error_message: str | None = None
    config_snapshot: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    candidate_rankings: list[CandidateRankingResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RankingStatusResponse(BaseModel):
    """Lightweight status check for a ranking run."""
    id: str
    status: str
    error_message: str | None = None
    progress: float | None = None
