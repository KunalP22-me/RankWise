"""Phase 8 tests — Overrides & Human-in-the-Loop Weight Recalibration."""

import pytest
from app.core.learning.weight_recalibration import recalibrate_weights_from_overrides
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.override import OverrideCreate
from app.services.override_service import OverrideService
from app.services.ranking_service import RankingService


class TestWeightRecalibrationMath:
    """Verify Ridge/Bayesian regression behavior on candidate overrides."""

    def test_recalibration_with_sparse_data(self):
        current_weights = {"must_have": 0.40, "nice_to_have": 0.20, "experience": 0.25, "education": 0.15}
        result = recalibrate_weights_from_overrides(
            current_weights=current_weights,
            candidate_ranking_records=[],
            overrides=[],
        )
        assert result["suggested_weights"] == current_weights
        assert result["total_overrides"] == 0

    def test_recalibration_upweights_must_haves(self):
        current_weights = {"must_have": 0.40, "nice_to_have": 0.20, "experience": 0.25, "education": 0.15}
        records = [
            {"id": "cr-1", "must_have_score": 0.95, "nice_to_have_score": 0.30, "experience_fit_score": 0.40, "education_fit_score": 0.30},
            {"id": "cr-2", "must_have_score": 0.90, "nice_to_have_score": 0.20, "experience_fit_score": 0.30, "education_fit_score": 0.30},
            {"id": "cr-3", "must_have_score": 0.85, "nice_to_have_score": 0.40, "experience_fit_score": 0.30, "education_fit_score": 0.30},
        ]
        # Overrides consistently push scores higher for strong must-have candidates
        overrides = [
            {"candidate_ranking_id": "cr-1", "criterion": "overall", "new_score": 0.98},
            {"candidate_ranking_id": "cr-2", "criterion": "overall", "new_score": 0.95},
            {"candidate_ranking_id": "cr-3", "criterion": "overall", "new_score": 0.90},
        ]
        result = recalibrate_weights_from_overrides(
            current_weights=current_weights,
            candidate_ranking_records=records,
            overrides=overrides,
            regularization_strength=0.5,
        )
        suggested = result["suggested_weights"]
        assert sum(suggested.values()) == pytest.approx(1.0, abs=0.01)
        # must_have weight should increase
        assert suggested["must_have"] >= current_weights["must_have"]
        assert len(result["pattern_summary"]) > 5


class TestOverrideServiceAndAPI:
    """Integration test: Execute ranking -> Add override -> Get suggestions -> Accept."""

    @pytest.fixture
    def setup_ranked_job(self, db_session):
        job = Job(
            title="Full Stack Tech Lead",
            description="Leading full stack architecture.",
            requirements={
                "must_have": [{"text": "Python", "type": "must_have", "category": "skill"}],
                "nice_to_have": [{"text": "Docker", "type": "nice_to_have", "category": "skill"}],
                "minimum_experience_years": 3,
                "education_requirement": "Bachelor's degree",
            },
            weights={"must_have": 0.40, "nice_to_have": 0.20, "experience": 0.25, "education": 0.15},
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        c1 = Candidate(
            job_id=job.id,
            filename="lead.pdf",
            file_path="lead.pdf",
            file_type="pdf",
            raw_text="Morgan Smith. 5 years Python and Docker development.",
            parsed_data={"name": "Morgan Smith", "skills": ["Python", "Docker"]},
            total_experience_years=5.0,
            status="parsed",
        )
        c2 = Candidate(
            job_id=job.id,
            filename="dev.pdf",
            file_path="dev.pdf",
            file_type="pdf",
            raw_text="Taylor Green. 3 years Python development.",
            parsed_data={"name": "Taylor Green", "skills": ["Python"]},
            total_experience_years=3.0,
            status="parsed",
        )
        db_session.add_all([c1, c2])
        db_session.commit()

        run = RankingService(db_session).execute_ranking(job.id)
        return job, run

    def test_create_override_flow(self, db_session, setup_ranked_job):
        job, run = setup_ranked_job
        cr = run.candidate_rankings[0]

        service = OverrideService(db_session)
        override_payload = OverrideCreate(
            criterion="overall",
            new_score=0.97,
            reason_category="domain_expertise",
            reason_text="Exceptional open-source track record verified during screening.",
        )
        resp = service.create_override(cr.id, override_payload, user="lead_recruiter")

        assert resp.candidate_ranking_id == cr.id
        assert resp.new_score == 0.97
        assert resp.reason_category == "domain_expertise"
        assert cr.overridden_score == 0.97

    def test_override_and_weight_suggestions_api(self, client, setup_ranked_job):
        job, run = setup_ranked_job
        cr1 = run.candidate_rankings[0]
        cr2 = run.candidate_rankings[1]

        # 1. Post overrides
        ov1_resp = client.post(
            f"/api/rankings/{cr1.id}/override",
            json={
                "criterion": "overall",
                "new_score": 0.99,
                "reason_category": "domain_expertise",
                "reason_text": "Strong open source contributions.",
            },
        )
        assert ov1_resp.status_code == 201

        ov2_resp = client.post(
            f"/api/rankings/{cr2.id}/override",
            json={
                "criterion": "overall",
                "new_score": 0.90,
                "reason_category": "domain_expertise",
                "reason_text": "Practical depth.",
            },
        )
        assert ov2_resp.status_code == 201

        # 2. Get weight suggestions
        sug_resp = client.get(f"/api/jobs/{job.id}/weight-suggestions")
        assert sug_resp.status_code == 200
        sug_data = sug_resp.json()
        assert sug_data["total_overrides_analyzed"] == 2
        assert "suggested_weights" in sug_data

        # 3. Accept suggestions
        new_weights = sug_data["suggested_weights"]
        accept_resp = client.post(
            f"/api/jobs/{job.id}/weight-suggestions/accept",
            json={"weights": new_weights},
        )
        assert accept_resp.status_code == 200
        assert accept_resp.json()["status"] == "success"
