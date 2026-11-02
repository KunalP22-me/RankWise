"""Phase 4 tests — Job description understanding, skill ontology, and exclusionary bias checks."""

import pytest
from app.core.jd import SkillOntology, check_jd_bias, extract_job_requirements, ontology
from app.models.job import Job
from app.schemas.job import JDBiasCheckResult, JobRequirements


class TestSkillOntology:
    """Verify skill synonym mapping and hierarchical similarity calculations."""

    def test_synonym_normalization(self):
        assert ontology.normalize("py") == "python"
        assert ontology.normalize("k8s") == "kubernetes"
        assert ontology.normalize("postgres") == "postgresql"
        assert ontology.normalize("ReactJS") == "react"

    def test_exact_and_synonym_similarity(self):
        assert ontology.get_similarity("python", "python") == 1.0
        assert ontology.get_similarity("py", "python") == 1.0
        assert ontology.get_similarity("k8s", "kubernetes") == 1.0

    def test_sibling_similarity_partial_credit(self):
        """Technologies under the same immediate parent receive 0.75 partial credit."""
        # FastAPI and Flask both share "python backend"
        assert ontology.get_similarity("fastapi", "flask") == 0.75
        # PyTorch and TensorFlow both share "deep learning"
        assert ontology.get_similarity("pytorch", "tensorflow") == 0.75
        # React and Vue both share "frontend frameworks"
        assert ontology.get_similarity("react", "vue") == 0.75

    def test_parent_child_similarity(self):
        """A framework and its parent domain receive 0.85 credit."""
        assert ontology.get_similarity("pytorch", "deep learning") == 0.85
        assert ontology.get_similarity("fastapi", "python backend") == 0.85

    def test_unrelated_skills_zero_similarity(self):
        assert ontology.get_similarity("python", "dentistry") == 0.0
        assert ontology.get_similarity("docker", "accounting") == 0.0


class TestJDExtraction:
    """Verify LLM-powered structured requirements and implied skills extraction."""

    def test_extract_requirements(self, db_session):
        jd_text = (
            "We are looking for a Senior Backend Engineer with 5+ years of Python experience. "
            "Must have hands-on experience designing and running high-throughput Kafka streaming pipelines. "
            "Nice to have: experience with PyTorch."
        )
        reqs = extract_job_requirements(jd_text, db=db_session)
        assert isinstance(reqs, JobRequirements)
        assert len(reqs.must_have) >= 1
        assert reqs.minimum_experience_years == 5
        assert "Senior" in (reqs.seniority_level or "")
        # Implied skills present
        assert len(reqs.implied_skills) > 0


class TestJDBiasCheck:
    """Verify detection of exclusionary and biased phrasing in job descriptions."""

    def test_detect_age_and_gender_bias(self, db_session):
        biased_jd = (
            "Seeking a young and energetic rockstar developer to join our fast-paced startup. "
            "Recent college grads only."
        )
        result = check_jd_bias(biased_jd, db=db_session)
        assert isinstance(result, JDBiasCheckResult)
        assert result.is_clean is False
        assert len(result.flags) >= 2

        issues = [f.issue.lower() for f in result.flags]
        assert any("age" in issue for issue in issues)

    def test_clean_inclusive_jd(self, db_session):
        clean_jd = (
            "We are seeking an experienced Backend Engineer to lead distributed systems design. "
            "Qualifications: 4+ years of professional software engineering in Python, experience "
            "with relational databases, and a collaborative team mindset."
        )
        result = check_jd_bias(clean_jd, db=db_session)
        assert isinstance(result, JDBiasCheckResult)
        assert result.is_clean is True
        assert len(result.flags) == 0


class TestJDEndpoints:
    """Verify FastAPI routes for JD requirement extraction and bias checking."""

    def test_extract_requirements_api(self, client, db_session):
        job = Job(
            title="Senior ML Engineer",
            description="5+ years Python required. Must build streaming pipelines with Kafka.",
        )
        db_session.add(job)
        db_session.commit()

        res = client.post(f"/api/jobs/{job.id}/extract-requirements")
        assert res.status_code == 200
        data = res.json()
        assert "must_have" in data
        assert len(data["must_have"]) > 0

        # Verify persisted on Job record
        db_session.refresh(job)
        assert job.requirements_json is not None

    def test_jd_bias_check_api(self, client, db_session):
        job = Job(
            title="Hacker Role",
            description="Looking for a rockstar hacker to crush code.",
        )
        db_session.add(job)
        db_session.commit()

        res = client.post(f"/api/jobs/{job.id}/jd-bias-check")
        assert res.status_code == 200
        data = res.json()
        assert "flags" in data
        assert data["is_clean"] is False

        # Verify persisted on Job record
        db_session.refresh(job)
        assert job.bias_check_results is not None
