"""Phase 6 tests — Deterministic Scoring, Evidence Judging, Explanations & Ranking Orchestration."""

import pytest
from fastapi.testclient import TestClient

from app.core.llm import MockLLMClient
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
from app.main import app
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.ranking_service import RankingService


class TestDeterministicScoringEngine:
    """Verify deterministic scoring rules where the LLM never sets numeric scores."""

    def test_verdict_weights(self):
        # Strong verdict
        score_strong = compute_requirement_score(
            verdict="Strong",
            semantic_similarity=0.85,
            location_weight=1.0,
            recency_weight=1.0,
            duration_weight=1.0,
        )
        assert 0.70 < score_strong <= 1.0

        # Partial verdict
        score_partial = compute_requirement_score(
            verdict="Partial",
            semantic_similarity=0.85,
            location_weight=1.0,
            recency_weight=1.0,
            duration_weight=1.0,
        )
        assert 0.30 < score_partial < score_strong

        # None verdict must strictly be 0.0 regardless of location or similarity
        score_none = compute_requirement_score(
            verdict="None",
            semantic_similarity=0.99,
            location_weight=1.0,
            recency_weight=1.0,
            duration_weight=1.0,
        )
        assert score_none == 0.0

    def test_evidence_location_weight(self):
        # Experience bullet > Project > Skills list > Education
        assert compute_evidence_location_weight("experience") > compute_evidence_location_weight("project")
        assert compute_evidence_location_weight("project") > compute_evidence_location_weight("skill")
        assert compute_evidence_location_weight("skill") > compute_evidence_location_weight("education")

    def test_recency_and_duration_weight(self):
        # Present/current roles have maximum recency
        assert compute_recency_weight({"end_date": "Present"}) == 1.0
        assert compute_recency_weight({"end_date": "2026-01"}) == 1.0
        assert compute_recency_weight({"end_date": "2018-01"}) < 1.0

        # 5+ years experience has maximum duration weight
        assert compute_duration_weight(6.0) == 1.0
        assert compute_duration_weight(1.0) < compute_duration_weight(6.0)

    def test_experience_and_education_fit(self):
        # Experience fit
        assert compute_experience_fit(candidate_years=6.0, required_years=5.0) == 1.0
        assert compute_experience_fit(candidate_years=2.5, required_years=5.0) == 0.5

        # Education fit
        cand_edu = [{"degree": "Bachelor of Science in Computer Science", "institution": "State University"}]
        assert compute_education_fit(cand_edu, "Bachelor's degree") == 1.0
        assert compute_education_fit(cand_edu, "Master's degree") == 0.75

    def test_overall_score_weighted_sum(self):
        weights = {
            "must_have": 0.50,
            "nice_to_have": 0.20,
            "experience": 0.20,
            "education": 0.10,
        }
        score = compute_overall_score(
            must_have_score=0.80,
            nice_to_have_score=0.60,
            experience_fit_score=1.0,
            education_fit_score=1.0,
            weights=weights,
        )
        # Expected: 0.5*0.8 + 0.2*0.6 + 0.2*1.0 + 0.1*1.0 = 0.40 + 0.12 + 0.20 + 0.10 = 0.82
        assert abs(score - 0.82) < 0.01


class TestEvidenceJudgingAndExplanation:
    """Verify evidence judging schema validation and grounded candidate explanations."""

    def test_evidence_judge_strong(self):
        mock_llm = MockLLMClient()
        verdict = judge_evidence(
            requirement_text="Production experience with Kafka",
            snippets=["Architected real-time streaming pipeline processing 10M events/day using Kafka and FastAPI."],
            llm=mock_llm,
        )
        assert verdict.verdict == "Strong"
        assert len(verdict.reason) > 5

    def test_evidence_judge_false_positive_hobby(self):
        mock_llm = MockLLMClient()
        verdict = judge_evidence(
            requirement_text="Production Python web development",
            snippets=["Member of weekly hobby gaming club and chess enthusiast."],
            llm=mock_llm,
        )
        assert verdict.verdict == "None"

    def test_grounded_explanation_generation(self):
        mock_llm = MockLLMClient()
        explanation = generate_candidate_explanation(
            job_title="Senior Backend Engineer",
            requirement_verdicts=[
                {"requirement_text": "Python", "verdict": "Strong", "verdict_reason": "Production API usage"},
                {"requirement_text": "Kafka", "verdict": "Strong", "verdict_reason": "Streaming pipeline"},
            ],
            candidate_evidence="6 years building distributed backend systems in Python and Kafka.",
            llm=mock_llm,
        )
        assert len(explanation.strengths) >= 1
        assert len(explanation.interview_questions) == 3
        assert len(explanation.summary) > 20


class TestRankingPipelineIntegration:
    """Integration test: Job + Candidates -> Two-Stage Retrieval -> Scoring -> RankingRun."""

    @pytest.fixture
    def test_job(self, db_session):
        job = Job(
            title="Senior Distributed Systems Engineer",
            description="We are seeking an experienced infrastructure engineer.",
            requirements={
                "must_have": [
                    {"text": "Python backend microservices experience", "type": "must_have", "category": "skill"},
                    {"text": "Production Apache Kafka event streaming", "type": "must_have", "category": "skill"},
                ],
                "nice_to_have": [
                    {"text": "Deep learning with PyTorch", "type": "nice_to_have", "category": "skill"},
                ],
                "minimum_experience_years": 4,
                "education_requirement": "Bachelor's degree in Computer Science",
            },
            weights={
                "must_have": 0.40,
                "nice_to_have": 0.20,
                "experience": 0.25,
                "education": 0.15,
            },
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    @pytest.fixture
    def sample_candidates(self, db_session, test_job):
        c1 = Candidate(
            job_id=test_job.id,
            filename="strong_candidate.pdf",
            file_path="uploads/strong_candidate.pdf",
            file_type="pdf",
            raw_text="Jordan Lee\nSenior Backend Engineer\n5 years experience building Kafka pipelines in Python.\nDegree: Bachelor of Science.",
            parsed_data={
                "name": "Jordan Lee",
                "skills": ["Python", "Kafka", "Docker", "FastAPI"],
                "work_experience": [
                    {
                        "company": "DataStream Corp",
                        "title": "Senior Pipeline Engineer",
                        "start_date": "2021-01",
                        "end_date": "Present",
                        "bullets": [
                            "Built distributed event streaming architecture with Kafka and Python.",
                            "Engineered real-time data pipelines processing 20k events/sec.",
                        ],
                    }
                ],
                "education": [{"degree": "Bachelor of Science", "institution": "Georgia Tech"}],
            },
            total_experience_years=5.0,
            status="parsed",
        )
        c2 = Candidate(
            job_id=test_job.id,
            filename="junior_candidate.pdf",
            file_path="uploads/junior_candidate.pdf",
            file_type="pdf",
            raw_text="Sam Taylor\nJunior Developer\nBasic HTML and hobby gaming club experience.",
            parsed_data={
                "name": "Sam Taylor",
                "skills": ["HTML", "CSS"],
                "work_experience": [
                    {
                        "company": "Local Shop",
                        "title": "Web Helper",
                        "start_date": "2023-01",
                        "end_date": "2023-12",
                        "bullets": ["Maintained basic web pages and hobby gaming club site."],
                    }
                ],
                "education": [{"degree": "High School Diploma", "institution": "West High"}],
            },
            total_experience_years=1.0,
            status="parsed",
        )
        db_session.add_all([c1, c2])
        db_session.commit()
        db_session.refresh(c1)
        db_session.refresh(c2)
        return [c1, c2]

    def test_execute_ranking_service(self, db_session, test_job, sample_candidates):
        service = RankingService(db_session)
        run = service.execute_ranking(test_job.id)

        assert run.status == "completed"
        assert len(run.candidate_rankings) == 2

        # Strong candidate should rank #1
        top_cand = run.candidate_rankings[0]
        second_cand = run.candidate_rankings[1]

        assert top_cand.rank == 1
        assert second_cand.rank == 2
        assert top_cand.overall_score > second_cand.overall_score
        assert top_cand.must_have_score > second_cand.must_have_score

        # Check evidence snippets and offsets
        assert top_cand.evidence_snippets is not None
        assert top_cand.explanation is not None
        assert "interview_questions" in top_cand.explanation

    def test_ranking_api_endpoints(self, client, test_job, sample_candidates):
        # Trigger synchronous ranking
        response = client.post(f"/api/jobs/{test_job.id}/rank?sync=true")
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "completed"

        # Fetch rankings
        get_resp = client.get(f"/api/jobs/{test_job.id}/rankings")
        assert get_resp.status_code == 200
        rankings_data = get_resp.json()

        assert rankings_data["job_id"] == test_job.id
        assert len(rankings_data["candidate_rankings"]) == 2
        assert rankings_data["candidate_rankings"][0]["rank"] == 1
        assert rankings_data["candidate_rankings"][0]["candidate_name"] == "Jordan Lee"
