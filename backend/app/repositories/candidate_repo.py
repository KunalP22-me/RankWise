"""Candidate repository — CRUD operations for Candidate model."""


from sqlalchemy.orm import Session

from app.models.candidate import Candidate


class CandidateRepository:
    """Data access layer for Candidate entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Candidate:
        """Create a new candidate."""
        candidate = Candidate(**kwargs)
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def get_by_id(self, candidate_id: str) -> Candidate | None:
        """Get a candidate by ID."""
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()

    def get_by_job(self, job_id: str, skip: int = 0, limit: int = 500) -> list[Candidate]:
        """Get all candidates for a job."""
        return (
            self.db.query(Candidate)
            .filter(Candidate.job_id == job_id)
            .order_by(Candidate.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, candidate_id: str, **kwargs) -> Candidate | None:
        """Update a candidate's fields."""
        candidate = self.get_by_id(candidate_id)
        if not candidate:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(candidate, key, value)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def delete(self, candidate_id: str) -> bool:
        """Delete a candidate by ID."""
        candidate = self.get_by_id(candidate_id)
        if not candidate:
            return False
        self.db.delete(candidate)
        self.db.commit()
        return True

    def bulk_create(self, candidates_data: list[dict]) -> list[Candidate]:
        """Create multiple candidates at once."""
        candidates = [Candidate(**data) for data in candidates_data]
        self.db.add_all(candidates)
        self.db.commit()
        for c in candidates:
            self.db.refresh(c)
        return candidates
