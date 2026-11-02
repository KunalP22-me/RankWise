"""Evaluation package — benchmark metrics, synthetic dataset, and baseline ATS."""

from app.core.evaluation.baseline_ats import BaselineATS
from app.core.evaluation.benchmark import (
    EvaluationHarness,
    compute_dcg,
    compute_mrr,
    compute_ndcg,
    compute_precision_at_k,
)
from app.core.evaluation.synthetic_data import BENCHMARK_ROLES

__all__ = [
    "BENCHMARK_ROLES",
    "BaselineATS",
    "EvaluationHarness",
    "compute_dcg",
    "compute_mrr",
    "compute_ndcg",
    "compute_precision_at_k",
]
