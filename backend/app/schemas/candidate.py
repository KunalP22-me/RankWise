"""Pydantic v2 schemas for candidates and parsed resume data."""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    """A single work experience entry."""
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None  # "Present" allowed
    bullets: list[str] = Field(default_factory=list)
    duration_months: int | None = None


class Education(BaseModel):
    """A single education entry."""
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    year: str | None = None


class Project(BaseModel):
    """A project entry from a resume."""
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    """Structured resume data extracted from parsing."""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class CandidateResponse(BaseModel):
    """Response body for a candidate."""
    id: str
    job_id: str
    filename: str
    file_type: str
    status: str
    parsed_data: dict | None = None
    parse_method: str | None = None
    parse_confidence: float | None = None
    parse_warnings: list | None = None
    total_experience_years: float | None = None
    raw_text: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
