"""Evaluation service — provides benchmark ablation results comparing ATS vs Embeddings vs Full System."""

import logging
from typing import Any
from app.core.evaluation.benchmark import EvaluationHarness
from app.core.evaluation.synthetic_data import BENCHMARK_ROLES
from app.schemas.evaluation import EvaluationResultResponse, MetricResult

logger = logging.getLogger("rankwise.evaluation_service")

# In-memory benchmark cache
_CACHED_BENCHMARKS: list[dict[str, Any]] | None = None


class EvaluationService:
    """Business logic for evaluation harness benchmarks."""

    def __init__(self):
        self.harness = EvaluationHarness()

    def get_evaluation_results(self, force_refresh: bool = False) -> list[EvaluationResultResponse]:
        """Run or return cached ablation benchmarks across all 3 benchmark job roles."""
        global _CACHED_BENCHMARKS
        if _CACHED_BENCHMARKS is not None and not force_refresh:
            return [EvaluationResultResponse.model_validate(r) for r in _CACHED_BENCHMARKS]

        results = []
        for role_data in BENCHMARK_ROLES:
            eval_res = self.harness.run_role_evaluation(role_data)
            results.append(eval_res)

        _CACHED_BENCHMARKS = results
        return [EvaluationResultResponse.model_validate(r) for r in results]
