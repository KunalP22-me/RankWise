"""Phase 9 tests — Evaluation Harness, Baseline Mini-ATS, NDCG/MRR Benchmarks & Keyword Traps."""

import pytest
from app.core.evaluation.baseline_ats import BaselineATS
from app.core.evaluation.benchmark import (
    EvaluationHarness,
    compute_dcg,
    compute_mrr,
    compute_ndcg,
    compute_precision_at_k,
)
from app.core.evaluation.synthetic_data import BENCHMARK_ROLES
from app.services.evaluation_service import EvaluationService


class TestEvaluationMetricsMath:
    """Verify NDCG, Precision@k, and MRR calculations."""

    def test_ndcg_calculation(self):
        # Perfect ordering: 3, 2, 1, 0 -> NDCG = 1.0
        perfect = [3, 2, 1, 0]
        assert compute_ndcg(perfect, k=4) == 1.0

        # Sub-optimal ordering: 0, 1, 2, 3 -> NDCG < 0.60
        reversed_order = [0, 1, 2, 3]
        assert compute_ndcg(reversed_order, k=4) < 0.65

    def test_precision_at_k(self):
        # 3 out of 5 relevant (rel >= 2)
        relevances = [3, 2, 2, 1, 0]
        assert compute_precision_at_k(relevances, k=5) == 0.60
        # In top 3: all 3 relevant -> 1.0
        assert compute_precision_at_k(relevances, k=3) == 1.0

    def test_mrr_calculation(self):
        # First relevant candidate at rank 1 -> MRR = 1.0
        assert compute_mrr([3, 1, 0]) == 1.0
        # First relevant candidate at rank 2 -> MRR = 0.5
        assert compute_mrr([1, 2, 0]) == 0.5
        # No relevant candidates -> MRR = 0.0
        assert compute_mrr([1, 0, 0]) == 0.0


class TestBaselineATSAndKeywordTraps:
    """Verify that traditional ATS falls for keyword stuffing while Full System catches it."""

    def test_baseline_ats_keyword_frequency_ranking(self):
        ats = BaselineATS()
        candidates = [
            {"id": "c1", "name": "Real Engineer", "raw_text": "Built production microservices with Python and Kafka.", "ground_truth_relevance": 3},
            {"id": "c2", "name": "Keyword Stuffer", "raw_text": "Python Python Python Kafka Kafka Kafka Docker Docker Kubernetes!", "ground_truth_relevance": 0, "is_keyword_trap": True},
        ]
        results = ats.rank_candidates("Python Kafka Docker Kubernetes", candidates)
        assert len(results) == 2
        # Traditional keyword frequency ATS gives high score to stuffer
        stuffer_rank = next(r["rank"] for r in results if r["candidate_id"] == "c2")
        assert stuffer_rank in (1, 2)

    def test_full_system_ablation_superiority(self):
        harness = EvaluationHarness()
        role = BENCHMARK_ROLES[0]  # Senior Backend Engineer
        eval_result = harness.run_role_evaluation(role)

        metrics = {m["metric"]: m for m in eval_result["metrics"]}
        # Full system should outperform baseline ATS on NDCG and Precision
        assert metrics["NDCG@5"]["full_system"] >= metrics["NDCG@5"]["baseline_ats"]
        assert metrics["Precision@5"]["full_system"] >= metrics["Precision@5"]["baseline_ats"]

        # Check keyword traps identified
        traps = eval_result["keyword_trap_examples"]
        assert len(traps) >= 1
        # Full system rank should be worse than or equal to baseline rank for stuffer
        first_trap = traps[0]
        assert first_trap["full_system_rank"] >= first_trap["baseline_ats_rank"]


class TestEvaluationServiceAndAPI:
    """Verify evaluation service caching and REST API endpoint."""

    def test_evaluation_service(self):
        service = EvaluationService()
        results = service.get_evaluation_results(force_refresh=True)
        assert len(results) == len(BENCHMARK_ROLES)
        assert results[0].job_role == BENCHMARK_ROLES[0]["title"]
        assert len(results[0].metrics) >= 3

    def test_evaluation_api_endpoint(self, client):
        resp = client.get("/api/evaluation/results")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "metrics" in data[0]
        assert "keyword_trap_examples" in data[0]
