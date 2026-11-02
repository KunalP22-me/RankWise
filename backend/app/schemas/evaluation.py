"""Pydantic v2 schemas for evaluation results."""


from pydantic import BaseModel, Field


class MetricResult(BaseModel):
    """A single metric result."""
    metric: str  # e.g., "NDCG@5", "MRR"
    baseline_ats: float
    embeddings_only: float
    full_system: float


class EvaluationResultResponse(BaseModel):
    """Complete evaluation harness results."""
    job_role: str
    metrics: list[MetricResult] = Field(default_factory=list)
    keyword_trap_examples: list[dict] = Field(default_factory=list)
    summary: str | None = None
