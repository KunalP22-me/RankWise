"""Phase 1 tests — database, models, CRUD, and API endpoints."""

from app.models import Candidate, Job
from app.repositories.audit_repo import AuditRepository
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository

# ═══════════════════════════════════════════
# Database & Model Tests
# ═══════════════════════════════════════════

class TestDatabaseCreation:
    """Verify tables are created correctly."""

    def test_tables_exist(self, db_session):
        """All expected tables should be created."""
        from sqlalchemy import inspect
        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()
        expected = [
            "jobs", "candidates", "ranking_runs", "candidate_rankings",
            "requirement_scores", "overrides", "audit_logs", "bias_reports",
        ]
        for table in expected:
            assert table in tables, f"Table '{table}' missing"


class TestJobModel:
    """Test Job ORM model."""

    def test_create_job(self, db_session):
        job = Job(title="Test Job", description="A test job description here.")
        db_session.add(job)
        db_session.commit()
        assert job.id is not None
        assert job.status == "draft"
        assert job.blind_mode is False
        assert job.weights is not None

    def test_job_default_weights(self, db_session):
        job = Job(title="Test", description="Description text here.")
        db_session.add(job)
        db_session.commit()
        assert job.weights["must_have"] == 0.40
        assert job.weights["nice_to_have"] == 0.15


class TestCandidateModel:
    """Test Candidate ORM model."""

    def test_create_candidate(self, db_session):
        job = Job(title="Test", description="Description here.")
        db_session.add(job)
        db_session.commit()

        candidate = Candidate(
            job_id=job.id,
            filename="resume.pdf",
            file_path="/tmp/resume.pdf",
            file_type="pdf",
        )
        db_session.add(candidate)
        db_session.commit()
        assert candidate.id is not None
        assert candidate.status == "uploaded"

    def test_cascade_delete(self, db_session):
        """Deleting a job should delete its candidates."""
        job = Job(title="Test", description="Description here.")
        db_session.add(job)
        db_session.commit()

        candidate = Candidate(
            job_id=job.id, filename="r.pdf", file_path="/tmp/r.pdf", file_type="pdf"
        )
        db_session.add(candidate)
        db_session.commit()
        cid = candidate.id

        db_session.delete(job)
        db_session.commit()
        assert db_session.query(Candidate).filter_by(id=cid).first() is None


# ═══════════════════════════════════════════
# Repository Tests
# ═══════════════════════════════════════════

class TestJobRepository:
    """Test JobRepository CRUD."""

    def test_create_and_get(self, db_session):
        repo = JobRepository(db_session)
        job = repo.create(title="Dev Role", description="Build things with code.")
        assert job.id
        fetched = repo.get_by_id(job.id)
        assert fetched.title == "Dev Role"

    def test_list_all(self, db_session):
        repo = JobRepository(db_session)
        repo.create(title="Job 1", description="Description one here.")
        repo.create(title="Job 2", description="Description two here.")
        jobs = repo.get_all()
        assert len(jobs) == 2

    def test_update(self, db_session):
        repo = JobRepository(db_session)
        job = repo.create(title="Old Title", description="Old description here.")
        updated = repo.update(job.id, title="New Title")
        assert updated.title == "New Title"

    def test_delete(self, db_session):
        repo = JobRepository(db_session)
        job = repo.create(title="To Delete", description="Will be deleted soon.")
        assert repo.delete(job.id) is True
        assert repo.get_by_id(job.id) is None

    def test_candidate_count(self, db_session):
        repo = JobRepository(db_session)
        job = repo.create(title="Job", description="Job description here.")
        assert repo.get_candidate_count(job.id) == 0

        c = Candidate(job_id=job.id, filename="r.pdf", file_path="/t", file_type="pdf")
        db_session.add(c)
        db_session.commit()
        assert repo.get_candidate_count(job.id) == 1


class TestCandidateRepository:
    """Test CandidateRepository CRUD."""

    def test_bulk_create(self, db_session):
        job = Job(title="J", description="Description content here.")
        db_session.add(job)
        db_session.commit()

        repo = CandidateRepository(db_session)
        candidates = repo.bulk_create([
            {"job_id": job.id, "filename": "a.pdf", "file_path": "/a", "file_type": "pdf"},
            {"job_id": job.id, "filename": "b.docx", "file_path": "/b", "file_type": "docx"},
        ])
        assert len(candidates) == 2
        assert all(c.id for c in candidates)


class TestAuditRepository:
    """Test AuditRepository."""

    def test_log_entry(self, db_session):
        repo = AuditRepository(db_session)
        entry = repo.log("test_action", detail={"key": "value"})
        assert entry.id
        assert entry.action == "test_action"

    def test_filter_by_job(self, db_session):
        repo = AuditRepository(db_session)
        repo.log("action1", job_id="job-1")
        repo.log("action2", job_id="job-2")
        logs = repo.get_by_job("job-1")
        assert len(logs) == 1


# ═══════════════════════════════════════════
# API Endpoint Tests
# ═══════════════════════════════════════════

class TestHealthEndpoint:
    """Test health check."""

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestJobsAPI:
    """Test Job CRUD API endpoints."""

    def test_create_job(self, client, sample_job_data):
        resp = client.post("/api/jobs", json=sample_job_data)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == sample_job_data["title"]
        assert data["status"] == "draft"
        assert "id" in data

    def test_list_jobs(self, client, sample_job_data):
        client.post("/api/jobs", json=sample_job_data)
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_job(self, client, sample_job_data):
        create_resp = client.post("/api/jobs", json=sample_job_data)
        job_id = create_resp.json()["id"]
        resp = client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    def test_get_nonexistent_job(self, client):
        resp = client.get("/api/jobs/nonexistent-id")
        assert resp.status_code == 404

    def test_update_job(self, client, sample_job_data):
        create_resp = client.post("/api/jobs", json=sample_job_data)
        job_id = create_resp.json()["id"]
        resp = client.put(f"/api/jobs/{job_id}", json={"title": "Updated Title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_delete_job(self, client, sample_job_data):
        create_resp = client.post("/api/jobs", json=sample_job_data)
        job_id = create_resp.json()["id"]
        resp = client.delete(f"/api/jobs/{job_id}")
        assert resp.status_code == 204
        assert client.get(f"/api/jobs/{job_id}").status_code == 404

    def test_create_job_validation(self, client):
        """Empty title should be rejected."""
        resp = client.post("/api/jobs", json={"title": "", "description": "Valid desc here."})
        assert resp.status_code == 422


class TestCandidatesAPI:
    """Test Candidate upload and list endpoints."""

    def test_list_empty_candidates(self, client, sample_job_data):
        create_resp = client.post("/api/jobs", json=sample_job_data)
        job_id = create_resp.json()["id"]
        resp = client.get(f"/api/jobs/{job_id}/candidates")
        assert resp.status_code == 200
        assert resp.json() == []
