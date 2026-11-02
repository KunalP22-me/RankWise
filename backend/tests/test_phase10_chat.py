"""Phase 10 tests — Grounded Recruiter Chat Assistant with Evidence Citations."""

import pytest
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService


class TestRecruiterChatAssistant:
    """Verify recruiter assistant grounding, snippet citations, and API responses."""

    @pytest.fixture
    def setup_job_with_candidates(self, db_session):
        job = Job(
            title="Principal Infrastructure Lead",
            description="Leading distributed cloud infrastructure.",
            requirements={
                "must_have": [{"text": "Apache Kafka", "type": "must_have", "category": "skill"}],
            },
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        c1 = Candidate(
            job_id=job.id,
            filename="alex.pdf",
            file_path="alex.pdf",
            file_type="pdf",
            raw_text="Alex Mercer. Architected real-time streaming pipeline processing 10M events/day using Kafka and FastAPI.",
            parsed_data={
                "name": "Alex Mercer",
                "work_experience": [
                    {
                        "company": "Nexus Technologies",
                        "title": "Senior Backend Engineer",
                        "bullets": [
                            "Architected real-time streaming pipeline processing 10M events/day using Kafka and FastAPI."
                        ],
                    }
                ],
            },
            status="parsed",
        )
        c2 = Candidate(
            job_id=job.id,
            filename="dev.pdf",
            file_path="dev.pdf",
            file_type="pdf",
            raw_text="Jamie Cole. Frontend web developer with React and CSS.",
            parsed_data={"name": "Jamie Cole", "skills": ["React", "CSS"]},
            status="parsed",
        )
        db_session.add_all([c1, c2])
        db_session.commit()
        return job

    def test_chat_service_finds_and_cites_evidence(self, db_session, setup_job_with_candidates):
        job = setup_job_with_candidates
        service = ChatService(db_session)

        response = service.answer_query(
            job_id=job.id,
            question="Who has production Kafka streaming experience?",
        )
        assert len(response.answer) > 10
        assert response.confidence in ("high", "medium", "low")
        assert len(response.cited_snippets) >= 1
        assert "Kafka" in response.cited_snippets[0].snippet or "Alex" in response.cited_snippets[0].snippet or "pipeline" in response.cited_snippets[0].snippet

    def test_chat_service_handles_empty_evidence(self, db_session, setup_job_with_candidates):
        job = setup_job_with_candidates
        service = ChatService(db_session)

        response = service.answer_query(
            job_id=job.id,
            question="Who has experience building iOS applications in Swift?",
        )
        assert "no evidence" in response.answer.lower() or response.confidence in ("low", "none")

    def test_chat_api_endpoint(self, client, setup_job_with_candidates):
        job = setup_job_with_candidates

        resp = client.post(
            f"/api/jobs/{job.id}/chat",
            json={"question": "Compare candidates with streaming experience."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "cited_snippets" in data
        assert "confidence" in data
