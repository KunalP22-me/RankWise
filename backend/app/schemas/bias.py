"""Pydantic v2 schemas for bias reports."""

from datetime import datetime

from pydantic import BaseModel


class BiasReportResponse(BaseModel):
    """Response body for a bias report."""
    id: str
    ranking_run_id: str
    adverse_impact: dict | None = None
    counterfactual_results: dict | None = None
    proxy_warnings: list | None = None
    summary: str | None = None
    flagged: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
