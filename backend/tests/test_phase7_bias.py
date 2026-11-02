"""Phase 7 tests — Bias Safeguards, Blind Redaction, Counterfactual Testing & Adverse Impact."""

import inspect
import pytest
from app.core.bias.adverse_impact import calculate_adverse_impact_ratios
from app.core.bias.blind_redactor import redact_parsed_data, redact_text
from app.core.bias.counterfactual import evaluate_counterfactual_delta, perturb_candidate_profile
from app.core.bias.proxy_detector import detect_proxy_correlations
from app.core.scoring import (
    compute_education_fit,
    compute_evidence_location_weight,
    compute_experience_fit,
    compute_overall_score,
    compute_recency_weight,
    compute_requirement_score,
)
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.bias_service import BiasService
from app.services.ranking_service import RankingService


class TestScorerAttributeIsolation:
    """CRITICAL AUDIT: The scorer must NEVER take protected attributes as input features."""

    FORBIDDEN_PROTECTED_ATTRIBUTES = {
        "gender", "sex", "race", "ethnicity", "name", "candidate_name",
        "age", "dob", "birth_date", "graduation_year", "religion",
        "disability", "nationality", "marital_status", "sexual_orientation",
    }

    def test_scoring_functions_never_accept_protected_attributes(self):
        """Assert that no scoring engine function accepts protected attributes as parameters."""
        scoring_functions = [
            compute_requirement_score,
            compute_overall_score,
            compute_experience_fit,
            compute_education_fit,
            compute_evidence_location_weight,
            compute_recency_weight,
        ]

        for fn in scoring_functions:
            sig = inspect.signature(fn)
            param_names = set(sig.parameters.keys())
            forbidden_found = param_names.intersection(self.FORBIDDEN_PROTECTED_ATTRIBUTES)
            assert not forbidden_found, (
                f"Scorer function {fn.__name__} violates fairness isolation: accepts protected attribute(s) {forbidden_found}"
            )


class TestBlindModeRedactor:
    """Verify blind mode scrubbing of PII, pronouns, age cues, and institutions."""

    def test_redact_personal_identifiers(self):
        raw_text = (
            "John Doe is a Senior Engineer. Contact: john.doe@email.com, (555) 234-5678. "
            "He graduated in 2002 from Harvard University. He built scalable microservices."
        )
        redacted = redact_text(
            raw_text,
            candidate_name="John Doe",
            candidate_email="john.doe@email.com",
            candidate_phone="(555) 234-5678",
            redact_institutions=True,
            institutions=["Harvard University"],
        )

        assert "John" not in redacted
        assert "Doe" not in redacted
        assert "john.doe@email.com" not in redacted
        assert "(555) 234-5678" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
        assert "[REDACTED_PHONE]" in redacted
        assert "[REDACTED_INSTITUTION]" in redacted
        # Pronoun replacement
        assert "they built scalable microservices" in redacted.lower()

    def test_redact_parsed_data_structure(self):
        parsed = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "555-987-6543",
            "location": "Boston, MA",
            "education": [
                {"degree": "B.S. CS", "institution": "MIT", "year": "2015"}
            ],
        }
        clean = redact_parsed_data(parsed, redact_institutions=True)
        assert clean["name"] == "[REDACTED_NAME]"
        assert clean["email"] == "[REDACTED_EMAIL]"
        assert clean["location"] == "[REDACTED_LOCATION]"
        assert clean["education"][0]["year"] is None
        assert clean["education"][0]["institution"] == "[REDACTED_INSTITUTION]"


class TestCounterfactualPerturbation:
    """Verify counterfactual signal swaps and score delta tracking."""

    def test_perturb_profile(self):
        name = "David Miller"
        raw_text = "David Miller is a backend specialist. He built real-time streaming tools."
        p_name, p_text, p_parsed, swaps = perturb_candidate_profile(name, raw_text, {"name": name})

        assert "Emily" in p_name or "Sarah" in p_name or "Priya" in p_name
        assert "she" in p_text.lower()
        assert len(swaps) >= 1

    def test_counterfactual_delta_flagging(self):
        # Under threshold: no flag
        stable = evaluate_counterfactual_delta(original_score=0.85, perturbed_score=0.86, delta_threshold=0.05)
        assert not stable["is_flagged"]
        assert stable["score_delta"] == 0.01

        # Over threshold: flagged
        unstable = evaluate_counterfactual_delta(original_score=0.85, perturbed_score=0.72, delta_threshold=0.05)
        assert unstable["is_flagged"]
        assert unstable["score_delta"] == 0.13


class TestAdverseImpactAndFourFifthsRule:
    """Verify EEOC four-fifths (80%) rule calculation."""

    def test_four_fifths_rule_compliant(self):
        # Equal shortlisting across cohorts
        candidates = [
            {"group": "Group A", "rank": 1, "overall_score": 0.90},
            {"group": "Group A", "rank": 2, "overall_score": 0.85},
            {"group": "Group B", "rank": 3, "overall_score": 0.82},
            {"group": "Group B", "rank": 4, "overall_score": 0.80},
        ]
        result = calculate_adverse_impact_ratios(candidates, top_k_shortlist=2)
        # Both groups have 1/2 shortlisted -> selection rate = 0.50 -> ratio = 1.0
        assert not result["four_fifths_violation"]

    def test_four_fifths_rule_violation_detected(self):
        # Group A has 100% selection, Group B has 0% selection
        candidates = [
            {"group": "Group A", "rank": 1, "overall_score": 0.95},
            {"group": "Group A", "rank": 2, "overall_score": 0.90},
            {"group": "Group B", "rank": 3, "overall_score": 0.40},
            {"group": "Group B", "rank": 4, "overall_score": 0.35},
        ]
        result = calculate_adverse_impact_ratios(candidates, top_k_shortlist=2)
        assert result["four_fifths_violation"]
        assert result["groups"]["Group B"]["impact_ratio"] < 0.80


class TestBiasServiceAndEndpoints:
    """Integration test: Ranking run -> Bias report generation -> REST API."""

    @pytest.fixture
    def setup_ranked_job(self, db_session):
        job = Job(
            title="Senior Infrastructure Architect",
            description="Leading core infrastructure systems.",
            requirements={
                "must_have": [{"text": "Python", "type": "must_have", "category": "skill"}],
                "nice_to_have": [],
                "minimum_experience_years": 3,
                "education_requirement": "Bachelor's degree",
            },
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        c1 = Candidate(
            job_id=job.id,
            filename="cand1.pdf",
            file_path="cand1.pdf",
            file_type="pdf",
            raw_text="Alice Walker. 5 years Python backend engineering.",
            parsed_data={"name": "Alice Walker", "skills": ["Python"]},
            total_experience_years=5.0,
            status="parsed",
        )
        c2 = Candidate(
            job_id=job.id,
            filename="cand2.pdf",
            file_path="cand2.pdf",
            file_type="pdf",
            raw_text="Bob Martin. 4 years Python microservices.",
            parsed_data={"name": "Bob Martin", "skills": ["Python"]},
            total_experience_years=4.0,
            status="parsed",
        )
        db_session.add_all([c1, c2])
        db_session.commit()

        # Run ranking
        rank_service = RankingService(db_session)
        run = rank_service.execute_ranking(job.id)
        return job, run

    def test_generate_and_fetch_bias_report(self, db_session, setup_ranked_job):
        job, run = setup_ranked_job
        bias_service = BiasService(db_session)
        report = bias_service.generate_bias_report(run.id)

        assert report.ranking_run_id == run.id
        assert report.adverse_impact is not None
        assert report.counterfactual_results is not None
        assert "Four-Fifths" in report.summary

    def test_bias_api_endpoints(self, client, setup_ranked_job):
        job, run = setup_ranked_job

        # GET bias report
        get_resp = client.get(f"/api/jobs/{job.id}/bias-report")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["ranking_run_id"] == run.id
        assert "adverse_impact" in data

        # POST counterfactual test
        cf_resp = client.post(f"/api/jobs/{job.id}/counterfactual-test")
        assert cf_resp.status_code == 200
        cf_data = cf_resp.json()
        assert cf_data["total_tested"] == 2
        assert cf_data["flagged_count"] == 0
