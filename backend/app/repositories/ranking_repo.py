"""Ranking repository — CRUD for RankingRun, CandidateRanking, RequirementScore."""


from sqlalchemy.orm import Session, joinedload

from app.models.override import Override
from app.models.ranking import CandidateRanking, RankingRun


class RankingRepository:
    """Data access layer for ranking entities."""

    def __init__(self, db: Session):
        self.db = db

    # ── RankingRun ──

    def create_run(self, **kwargs) -> RankingRun:
        """Create a new ranking run."""
        run = RankingRun(**kwargs)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: str) -> RankingRun | None:
        """Get a ranking run by ID with candidate rankings eagerly loaded."""
        return (
            self.db.query(RankingRun)
            .options(joinedload(RankingRun.candidate_rankings))
            .filter(RankingRun.id == run_id)
            .first()
        )

    def get_runs_by_job(self, job_id: str) -> list[RankingRun]:
        """Get all ranking runs for a job."""
        return (
            self.db.query(RankingRun)
            .filter(RankingRun.job_id == job_id)
            .order_by(RankingRun.created_at.desc())
            .all()
        )

    def get_latest_run(self, job_id: str) -> RankingRun | None:
        """Get the most recent completed ranking run for a job."""
        return (
            self.db.query(RankingRun)
            .options(joinedload(RankingRun.candidate_rankings))
            .filter(RankingRun.job_id == job_id, RankingRun.status == "completed")
            .order_by(RankingRun.created_at.desc())
            .first()
        )

    def update_run(self, run_id: str, **kwargs) -> RankingRun | None:
        """Update a ranking run's fields."""
        run = self.db.query(RankingRun).filter(RankingRun.id == run_id).first()
        if not run:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(run, key, value)
        self.db.commit()
        self.db.refresh(run)
        return run

    # ── CandidateRanking ──

    def create_candidate_ranking(self, **kwargs) -> CandidateRanking:
        """Create a candidate ranking entry."""
        cr = CandidateRanking(**kwargs)
        self.db.add(cr)
        self.db.commit()
        self.db.refresh(cr)
        return cr

    def get_candidate_ranking(self, cr_id: str) -> CandidateRanking | None:
        """Get a candidate ranking by ID."""
        return (
            self.db.query(CandidateRanking)
            .options(joinedload(CandidateRanking.overrides))
            .filter(CandidateRanking.id == cr_id)
            .first()
        )

    def get_rankings_by_run(self, run_id: str) -> list[CandidateRanking]:
        """Get all candidate rankings for a run, ordered by rank."""
        return (
            self.db.query(CandidateRanking)
            .filter(CandidateRanking.ranking_run_id == run_id)
            .order_by(CandidateRanking.rank)
            .all()
        )

    def update_candidate_ranking(self, cr_id: str, **kwargs) -> CandidateRanking | None:
        """Update a candidate ranking."""
        cr = self.db.query(CandidateRanking).filter(CandidateRanking.id == cr_id).first()
        if not cr:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(cr, key, value)
        self.db.commit()
        self.db.refresh(cr)
        return cr

    # ── Override ──

    def create_override(self, **kwargs) -> Override:
        """Create an override entry."""
        override = Override(**kwargs)
        self.db.add(override)
        self.db.commit()
        self.db.refresh(override)
        return override

    def get_overrides_by_job(self, job_id: str) -> list[Override]:
        """Get all overrides for a job (via ranking runs)."""
        return (
            self.db.query(Override)
            .join(CandidateRanking)
            .join(RankingRun)
            .filter(RankingRun.job_id == job_id)
            .order_by(Override.created_at.desc())
            .all()
        )

    # ── Bulk operations ──

    def bulk_create_candidate_rankings(self, rankings_data: list[dict]) -> list[CandidateRanking]:
        """Create multiple candidate rankings at once."""
        rankings = [CandidateRanking(**data) for data in rankings_data]
        self.db.add_all(rankings)
        self.db.commit()
        for r in rankings:
            self.db.refresh(r)
        return rankings
