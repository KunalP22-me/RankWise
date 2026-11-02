"""Pydantic v2 schemas for recruiter assistant chat."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Recruiter chat inquiry."""
    question: str = Field(..., min_length=2, max_length=1000)


class CitedSnippet(BaseModel):
    """Evidence snippet cited by chat assistant."""
    candidate_id: str | None = None
    candidate_name: str | None = None
    snippet: str
    relevance: str | None = None


class ChatResponse(BaseModel):
    """Assistant grounded response."""
    answer: str
    cited_snippets: list[CitedSnippet] = Field(default_factory=list)
    confidence: str = Field(default="medium", pattern="^(high|medium|low|none)$")
