"""Pydantic v2 schemas for jobs, requirements, and JD bias checks."""

from datetime import datetime

from pydantic import BaseModel, Field

# ── Requirements ──

class Requirement(BaseModel):
    """A single requirement extracted from a job description."""
    text: str = Field(..., description="The requirement text")
    type: str = Field(..., pattern="^(must_have|nice_to_have)$")
    category: str | None = Field(None, description="e.g., skill, experience, education")
    implied_skills: list[str] = Field(default_factory=list)


class JobRequirements(BaseModel):
    """Structured requirements extracted from a JD by the LLM."""
    must_have: list[Requirement] = Field(default_factory=list)
    nice_to_have: list[Requirement] = Field(default_factory=list)
    minimum_experience_years: int | None = None
    seniority_level: str | None = None
    education_requirement: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    implied_skills: list[str] = Field(default_factory=list)


class WeightConfig(BaseModel):
    """Criterion weights for scoring (must sum to ~1.0)."""
    must_have: float = 0.40
    nice_to_have: float = 0.15
    experience_fit: float = 0.25
    education_fit: float = 0.20


# ── JD Bias ──

class BiasFlag(BaseModel):
    """A single bias flag found in a JD."""
    original_text: str
    issue: str
    suggestion: str
    severity: str = Field(..., pattern="^(high|medium|low)$")


class JDBiasCheckResult(BaseModel):
    """Result of a JD bias check."""
    flags: list[BiasFlag] = Field(default_factory=list)
    overall_assessment: str = ""
    is_clean: bool = True


# ── Job CRUD ──

class JobCreate(BaseModel):
    """Request body for creating a job."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=10)
    blind_mode: bool = False
    weights: WeightConfig | None = None


class JobUpdate(BaseModel):
    """Request body for updating a job."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=10)
    status: str | None = Field(None, pattern="^(draft|active|closed)$")
    blind_mode: bool | None = None
    weights: WeightConfig | None = None
    requirements_json: dict | None = None


class JobResponse(BaseModel):
    """Response body for a job."""
    id: str
    title: str
    description: str
    status: str
    requirements_json: dict | None = None
    weights: dict | None = None
    bias_check_results: dict | None = None
    blind_mode: bool
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0

    model_config = {"from_attributes": True}
