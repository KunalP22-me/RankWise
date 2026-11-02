"""Pydantic v2 schemas for LLM structured outputs."""


from pydantic import BaseModel, Field


class LLMResumeExtraction(BaseModel):
    """Schema the LLM must return when extracting resume data."""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    work_experience: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class LLMEvidenceVerdict(BaseModel):
    """Schema for LLM evidence judgment per requirement."""
    verdict: str = Field(..., pattern="^(Strong|Partial|None)$")
    reason: str = Field(..., max_length=500)


class LLMCandidateExplanation(BaseModel):
    """Schema for LLM candidate explanation."""
    strengths: list[str] = Field(default_factory=list, max_length=5)
    gaps: list[str] = Field(default_factory=list, max_length=5)
    interview_questions: list[str] = Field(default_factory=list, max_length=3)
    summary: str = Field(default="", max_length=2000)


class LLMChatResponse(BaseModel):
    """Schema for LLM chat assistant response."""
    answer: str
    cited_snippets: list[dict] = Field(default_factory=list)
    confidence: str = Field(default="medium", pattern="^(high|medium|low|none)$")
