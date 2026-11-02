"""Pydantic v2 schemas for score overrides."""

from datetime import datetime

from pydantic import BaseModel, Field


class OverrideCreate(BaseModel):
    """Request body for creating a score override."""
    criterion: str = Field(
        default="overall",
        description=(
            "Which score to override: overall, must_have, nice_to_have, "
            "experience_fit, education_fit"
        ),
    )
    new_score: float = Field(..., ge=0.0, le=1.0)
    reason_category: str = Field(
        ...,
        description="Category: domain_expertise, culture_fit, incorrect_parsing, "
                    "missing_context, overqualified, underqualified, other",
    )
    reason_text: str | None = None


class OverrideResponse(BaseModel):
    """Response body for an override."""
    id: str
    candidate_ranking_id: str
    criterion: str
    original_score: float
    new_score: float
    reason_category: str
    reason_text: str | None = None
    user: str = "recruiter"
    created_at: datetime
    model_config = {"from_attributes": True}


class WeightSuggestionResponse(BaseModel):
    """Suggested weight recalibration based on recruiter overrides."""
    job_id: str
    current_weights: dict[str, float]
    suggested_weights: dict[str, float]
    total_overrides_analyzed: int
    pattern_summary: str
    confidence: float
