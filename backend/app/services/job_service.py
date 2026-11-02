"""Job service — business logic for job management."""


from sqlalchemy.orm import Session

from app.models.job import Job
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobCreate, JobResponse, JobUpdate


class JobService:
    """Business logic for jobs."""

    def __init__(self, db: Session):
        self.repo = JobRepository(db)

    def create_job(self, data: JobCreate) -> JobResponse:
        """Create a new job posting."""
        kwargs = data.model_dump(exclude_none=True)
        weights = kwargs.get("weights")
        if weights and not isinstance(weights, dict):
            kwargs["weights"] = weights.model_dump()
        job = self.repo.create(**kwargs)
        return self._to_response(job)

    def get_job(self, job_id: str) -> JobResponse | None:
        """Get a job by ID."""
        job = self.repo.get_by_id(job_id)
        if not job:
            return None
        return self._to_response(job)

    def list_jobs(self, skip: int = 0, limit: int = 100) -> list[JobResponse]:
        """List all jobs."""
        jobs = self.repo.get_all(skip=skip, limit=limit)
        return [self._to_response(j) for j in jobs]

    def update_job(self, job_id: str, data: JobUpdate) -> JobResponse | None:
        """Update a job."""
        kwargs = data.model_dump(exclude_none=True)
        weights = kwargs.get("weights")
        if weights and not isinstance(weights, dict):
            kwargs["weights"] = weights.model_dump()
        job = self.repo.update(job_id, **kwargs)
        if not job:
            return None
        return self._to_response(job)

    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        return self.repo.delete(job_id)

    def extract_requirements(self, job_id: str):
        """Extract structured requirements from job description."""
        job = self.repo.get_by_id(job_id)
        if not job:
            return None
        from app.core.jd import extract_job_requirements
        reqs = extract_job_requirements(job.description, db=self.repo.db)
        updated_job = self.repo.update(job_id, requirements_json=reqs.model_dump())
        return reqs

    def check_bias(self, job_id: str):
        """Analyze job description for exclusionary bias."""
        job = self.repo.get_by_id(job_id)
        if not job:
            return None
        from app.core.jd import check_jd_bias
        result = check_jd_bias(job.description, db=self.repo.db)
        self.repo.update(job_id, bias_check_results=result.model_dump())
        return result

    def _to_response(self, job: Job) -> JobResponse:
        """Convert ORM model to response schema."""
        return JobResponse(
            id=job.id,
            title=job.title,
            description=job.description,
            status=job.status,
            requirements_json=job.requirements_json,
            weights=job.weights,
            bias_check_results=job.bias_check_results,
            blind_mode=job.blind_mode,
            created_at=job.created_at,
            updated_at=job.updated_at,
            candidate_count=self.repo.get_candidate_count(job.id),
        )
