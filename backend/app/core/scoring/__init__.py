"""Scoring package — deterministic scoring, LLM evidence judging, and candidate explanations."""

from app.core.scoring.engine import (
    compute_duration_weight,
    compute_education_fit,
    compute_evidence_location_weight,
    compute_experience_fit,
    compute_overall_score,
    compute_recency_weight,
    compute_requirement_score,
)
from app.core.scoring.evidence_judge import judge_evidence
from app.core.scoring.explainer import generate_candidate_explanation

__all__ = [
    "compute_duration_weight",
    "compute_education_fit",
    "compute_evidence_location_weight",
    "compute_experience_fit",
    "compute_overall_score",
    "compute_recency_weight",
    "compute_requirement_score",
    "generate_candidate_explanation",
    "judge_evidence",
]
