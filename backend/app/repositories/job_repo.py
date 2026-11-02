"""Job repository — CRUD operations for Job model."""


from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job import Job


class JobRepository:
    """Data access layer for Job entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Job:
        """Create a new job."""
        job = Job(**kwargs)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_id(self, job_id: str) -> Job | None:
        """Get a job by ID."""
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Job]:
        """Get all jobs with pagination."""
        return self.db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    def update(self, job_id: str, **kwargs) -> Job | None:
        """Update a job's fields."""
        job = self.get_by_id(job_id)
        if not job:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(job, key, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, job_id: str) -> bool:
        """Delete a job by ID."""
        job = self.get_by_id(job_id)
        if not job:
            return False
        self.db.delete(job)
        self.db.commit()
        return True

    def get_candidate_count(self, job_id: str) -> int:
        """Get number of candidates for a job."""
        return (
            self.db.query(func.count(Candidate.id))
            .filter(Candidate.job_id == job_id)
            .scalar()
            or 0
        )
