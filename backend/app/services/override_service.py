"""Override service — records recruiter adjustments and computes learned weight suggestions."""

from datetime import UTC, datetime
import logging
from typing import Any
from sqlalchemy.orm import Session

from app.core.learning.weight_recalibration import recalibrate_weights_from_overrides
from app.models.audit_log import AuditLog
from app.models.job import Job
from app.models.override import Override
from app.models.ranking import CandidateRanking, RankingRun
from app.repositories.job_repo import JobRepository
from app.repositories.ranking_repo import RankingRepository
from app.schemas.override import OverrideCreate, OverrideResponse, WeightSuggestionResponse

logger = logging.getLogger("rankwise.override_service")


class OverrideService:
    """Business logic for recruiter overrides and human-in-the-loop recalibration."""

    def __init__(self, db: Session):
        self.db = db
        self.ranking_repo = RankingRepository(db)
        self.job_repo = JobRepository(db)

    def create_override(
        self,
        ranking_id: str,
        override_data: OverrideCreate,
        user: str = "recruiter",
    ) -> OverrideResponse:
        """Create a score override, update candidate ranking, and log to audit."""
        cr = self.ranking_repo.get_candidate_ranking(ranking_id)
        if not cr:
            raise ValueError(f"Candidate ranking {ranking_id} not found.")

        # Determine original score based on criterion
        orig_score = cr.overall_score
        if override_data.criterion == "must_have":
            orig_score = cr.must_have_score
            cr.must_have_score = override_data.new_score
        elif override_data.criterion == "nice_to_have":
            orig_score = cr.nice_to_have_score
            cr.nice_to_have_score = override_data.new_score
        elif override_data.criterion in ("experience", "experience_fit"):
            orig_score = cr.experience_fit_score
            cr.experience_fit_score = override_data.new_score
        elif override_data.criterion in ("education", "education_fit"):
            orig_score = cr.education_fit_score
            cr.education_fit_score = override_data.new_score

        # Set overridden overall score
        cr.overridden_score = override_data.new_score

        # Create Override record
        override = Override(
            candidate_ranking_id=ranking_id,
            criterion=override_data.criterion,
            original_score=orig_score,
            new_score=override_data.new_score,
            reason_category=override_data.reason_category,
            reason_text=override_data.reason_text,
            user=user,
            created_at=datetime.now(UTC),
        )
        self.db.add(override)

        # Audit log entry
        run = self.ranking_repo.get_run(cr.ranking_run_id)
        job_id = run.job_id if run else None

        audit = AuditLog(
            action="recruiter_override",
            job_id=job_id,
            user=user,
            detail={
                "candidate_ranking_id": ranking_id,
                "criterion": override_data.criterion,
                "original_score": orig_score,
                "new_score": override_data.new_score,
                "reason_category": override_data.reason_category,
                "reason_text": override_data.reason_text,
                "user": user,
            },
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(override)

        return OverrideResponse.model_validate(override)

    def get_weight_suggestions(self, job_id: str) -> WeightSuggestionResponse:
        """Compute suggested criterion weights from logged overrides."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        # Gather overrides for this job
        overrides = self.ranking_repo.get_overrides_by_job(job_id)

        # Gather candidate ranking records across ranking runs
        runs = self.ranking_repo.get_runs_by_job(job_id)
        cr_records: list[dict[str, Any]] = []
        for r in runs:
            for cr in r.candidate_rankings:
                cr_records.append({
                    "id": cr.id,
                    "overall_score": cr.overall_score,
                    "must_have_score": cr.must_have_score,
                    "nice_to_have_score": cr.nice_to_have_score,
                    "experience_fit_score": cr.experience_fit_score,
                    "education_fit_score": cr.education_fit_score,
                })

        ov_dicts = [
            {
                "candidate_ranking_id": ov.candidate_ranking_id,
                "criterion": ov.criterion,
                "original_score": ov.original_score,
                "new_score": ov.new_score,
                "reason_category": ov.reason_category,
            }
            for ov in overrides
        ]

        result = recalibrate_weights_from_overrides(
            current_weights=job.weights or {
                "must_have": 0.40,
                "nice_to_have": 0.20,
                "experience": 0.25,
                "education": 0.15,
            },
            candidate_ranking_records=cr_records,
            overrides=ov_dicts,
        )

        return WeightSuggestionResponse(
            job_id=job_id,
            current_weights=result["current_weights"],
            suggested_weights=result["suggested_weights"],
            total_overrides_analyzed=result["total_overrides"],
            pattern_summary=result["pattern_summary"],
            confidence=result["confidence"],
        )

    def accept_weight_suggestions(self, job_id: str, new_weights: dict[str, float]) -> dict[str, Any]:
        """Apply recruiter-approved weight changes to the job."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        # Normalize weights to sum to 1.0
        total = sum(new_weights.values()) or 1.0
        normalized = {k: round(v / total, 3) for k, v in new_weights.items()}

        old_weights = job.weights
        job.weights = normalized

        # Log audit entry
        audit = AuditLog(
            action="accepted_weight_recalibration",
            job_id=job_id,
            detail={"old_weights": old_weights, "new_weights": normalized},
        )
        self.db.add(audit)
        self.db.commit()

        return {
            "status": "success",
            "job_id": job_id,
            "weights": normalized,
            "message": "Job criterion weights successfully recalibrated based on recruiter overrides.",
        }
