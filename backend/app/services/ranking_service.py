"""Ranking service — orchestrates candidate ranking runs with deterministic scoring."""

from datetime import UTC, datetime
import logging
from typing import Any
from sqlalchemy.orm import Session

from app.core.embeddings.chunker import chunk_resume
from app.core.embeddings.retriever import two_stage_retriever
from app.core.llm import get_llm_client
from app.core.scoring.engine import (
    compute_duration_weight,
    compute_education_fit,
    compute_evidence_location_weight,
    compute_experience_fit,
    compute_overall_score,
    compute_recency_weight,
    compute_requirement_score,
)
from app.core.scoring.evidence_judge import judge_evidence
from app.core.scoring.explainer import generate_candidate_explanation
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.ranking import CandidateRanking, RankingRun
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.ranking_repo import RankingRepository
from app.schemas.job import Requirement
from app.schemas.ranking import CandidateRankingResponse, RankingRunResponse, RankingStatusResponse

logger = logging.getLogger("rankwise.ranking_service")


class RankingService:
    """Business logic for ranking candidate applications against job requirements."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RankingRepository(db)
        self.job_repo = JobRepository(db)
        self.candidate_repo = CandidateRepository(db)

    def execute_ranking(self, job_id: str) -> RankingRun:
        """Run candidate ranking synchronously and persist results."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job with id {job_id} not found.")

        candidates = self.candidate_repo.get_by_job(job_id)

        # Create new ranking run
        run = self.repo.create_run(
            job_id=job_id,
            status="running",
            started_at=datetime.now(UTC),
            config_snapshot=job.weights,
        )

        if not candidates:
            run = self.repo.update_run(
                run.id,
                status="completed",
                completed_at=datetime.now(UTC),
            )
            return run

        try:
            # Build Requirement objects from Job requirements
            req_data = job.requirements or {}
            must_haves = [
                Requirement(
                    text=r["text"] if isinstance(r, dict) else str(r),
                    type="must_have",
                    category=r.get("category", "skill") if isinstance(r, dict) else "skill",
                )
                for r in req_data.get("must_have", [])
            ]
            nice_to_haves = [
                Requirement(
                    text=r["text"] if isinstance(r, dict) else str(r),
                    type="nice_to_have",
                    category=r.get("category", "skill") if isinstance(r, dict) else "skill",
                )
                for r in req_data.get("nice_to_have", [])
            ]

            all_requirements = must_haves + nice_to_haves
            if not all_requirements:
                # Fallback requirement using job title if no requirements extracted
                all_requirements = [
                    Requirement(
                        text=f"Demonstrated technical qualifications for {job.title}",
                        type="must_have",
                        category="experience",
                    )
                ]

            llm = get_llm_client(db=self.db)
            min_years = req_data.get("minimum_experience_years", 0)
            edu_req = req_data.get("education_requirement")

            evaluated_candidates: list[dict[str, Any]] = []

            for candidate in candidates:
                parsed = candidate.parsed_data or {}
                raw_text = candidate.raw_text or ""
                chunks = chunk_resume(parsed, raw_text)

                # Two-stage retrieval
                match_results = two_stage_retriever.match_requirements_to_chunks(
                    chunks=chunks,
                    requirements=all_requirements,
                    stage1_top_k=5,
                )

                req_scores: list[dict[str, Any]] = []
                must_have_scores: list[float] = []
                nice_to_have_scores: list[float] = []
                verdicts_summary: list[dict[str, Any]] = []
                evidence_snippets: list[dict[str, Any]] = []

                for match in match_results:
                    req_text = match["requirement_text"]
                    req_type = match["requirement_type"]
                    best_chunk = match["best_chunk"]
                    top_cands = match.get("top_candidates", [])

                    snippets = [c["text"] for c in top_cands if c.get("text")]
                    if not snippets and best_chunk:
                        snippets = [best_chunk.text]

                    # LLM Evidence Verdict (Strong / Partial / None)
                    verdict_obj = judge_evidence(req_text, snippets, llm)

                    loc_w = (
                        compute_evidence_location_weight(best_chunk.chunk_type)
                        if best_chunk
                        else 0.40
                    )
                    rec_w = (
                        compute_recency_weight(best_chunk.metadata)
                        if best_chunk
                        else 0.75
                    )
                    dur_w = compute_duration_weight(candidate.total_experience_years or 0.0)

                    # Compute deterministic score strictly in code
                    num_score = compute_requirement_score(
                        verdict=verdict_obj.verdict,
                        semantic_similarity=match["semantic_similarity"],
                        location_weight=loc_w,
                        recency_weight=rec_w,
                        duration_weight=dur_w,
                    )

                    req_score_entry = {
                        "requirement_text": req_text,
                        "requirement_type": req_type,
                        "verdict": verdict_obj.verdict,
                        "verdict_reason": verdict_obj.reason,
                        "semantic_similarity": match["semantic_similarity"],
                        "final_score": num_score,
                        "snippet_text": best_chunk.text if best_chunk else None,
                        "snippet_start": best_chunk.start_char if best_chunk else None,
                        "snippet_end": best_chunk.end_char if best_chunk else None,
                    }
                    req_scores.append(req_score_entry)

                    if req_type == "must_have":
                        must_have_scores.append(num_score)
                    else:
                        nice_to_have_scores.append(num_score)

                    verdicts_summary.append({
                        "requirement_text": req_text,
                        "verdict": verdict_obj.verdict,
                        "verdict_reason": verdict_obj.reason,
                    })

                    if best_chunk:
                        evidence_snippets.append({
                            "requirement": req_text,
                            "snippet": best_chunk.text,
                            "verdict": verdict_obj.verdict,
                            "start_char": best_chunk.start_char,
                            "end_char": best_chunk.end_char,
                        })

                # Component scores
                avg_must_have = (
                    sum(must_have_scores) / max(1, len(must_have_scores))
                    if must_have_scores
                    else 1.0
                )
                avg_nice_to_have = (
                    sum(nice_to_have_scores) / max(1, len(nice_to_have_scores))
                    if nice_to_have_scores
                    else 1.0
                )
                exp_fit = compute_experience_fit(candidate.total_experience_years or 0.0, min_years)
                edu_fit = compute_education_fit(parsed.get("education", []), edu_req)

                overall = compute_overall_score(
                    must_have_score=avg_must_have,
                    nice_to_have_score=avg_nice_to_have,
                    experience_fit_score=exp_fit,
                    education_fit_score=edu_fit,
                    weights=job.weights,
                )

                # Gap analysis
                gaps = [
                    v["requirement_text"]
                    for v in verdicts_summary
                    if v["verdict"] == "None"
                ]

                # Grounded candidate explanation
                explanation_obj = generate_candidate_explanation(
                    job_title=job.title,
                    requirement_verdicts=verdicts_summary,
                    candidate_evidence=raw_text,
                    llm=llm,
                )

                evaluated_candidates.append({
                    "candidate_id": candidate.id,
                    "overall_score": overall,
                    "must_have_score": avg_must_have,
                    "nice_to_have_score": avg_nice_to_have,
                    "experience_fit_score": exp_fit,
                    "education_fit_score": edu_fit,
                    "requirement_scores": req_scores,
                    "gap_analysis": gaps,
                    "explanation": explanation_obj.model_dump(),
                    "evidence_snippets": evidence_snippets,
                })

            # Sort by overall score descending
            evaluated_candidates.sort(key=lambda x: x["overall_score"], reverse=True)

            # Persist candidate rankings with ranks
            rankings_to_create = []
            for rank_idx, cand_eval in enumerate(evaluated_candidates, start=1):
                cand_eval["ranking_run_id"] = run.id
                cand_eval["rank"] = rank_idx
                rankings_to_create.append(cand_eval)

            self.repo.bulk_create_candidate_rankings(rankings_to_create)

            # Mark run completed
            run = self.repo.update_run(
                run.id,
                status="completed",
                completed_at=datetime.now(UTC),
            )
            return run

        except Exception as e:
            logger.error(f"Ranking execution failed for job {job_id}: {e}", exc_info=True)
            run = self.repo.update_run(
                run.id,
                status="failed",
                error_message=str(e),
                completed_at=datetime.now(UTC),
            )
            return run

    def get_rankings(self, job_id: str) -> RankingRunResponse | None:
        """Get the latest completed ranking run for a job."""
        run = self.repo.get_latest_run(job_id)
        if not run:
            return None
        return self._build_run_response(run)

    def get_run_status(self, run_id: str) -> RankingStatusResponse | None:
        """Check status of a ranking run."""
        run = self.repo.get_run(run_id)
        if not run:
            return None
        return RankingStatusResponse(
            id=run.id,
            status=run.status,
            error_message=run.error_message,
        )

    def _build_run_response(self, run: RankingRun) -> RankingRunResponse:
        """Enrich CandidateRanking with candidate names and filenames."""
        candidate_map = {
            c.id: c
            for c in self.candidate_repo.get_by_job(run.job_id)
        }

        cand_responses = []
        sorted_rankings = sorted(run.candidate_rankings, key=lambda x: x.rank if x.rank is not None else 9999)
        for cr in sorted_rankings:
            cand = candidate_map.get(cr.candidate_id)
            cand_name = None
            cand_file = None
            if cand:
                cand_name = (cand.parsed_data or {}).get("name") or cand.filename
                cand_file = cand.filename

            cr_resp = CandidateRankingResponse(
                id=cr.id,
                candidate_id=cr.candidate_id,
                rank=cr.rank,
                overall_score=cr.overall_score,
                must_have_score=cr.must_have_score,
                nice_to_have_score=cr.nice_to_have_score,
                experience_fit_score=cr.experience_fit_score,
                education_fit_score=cr.education_fit_score,
                overridden_score=cr.overridden_score,
                requirement_scores=cr.requirement_scores,
                gap_analysis=cr.gap_analysis,
                explanation=cr.explanation,
                evidence_snippets=cr.evidence_snippets,
                created_at=cr.created_at,
                candidate_name=cand_name,
                candidate_filename=cand_file,
            )
            cand_responses.append(cr_resp)

        return RankingRunResponse(
            id=run.id,
            job_id=run.job_id,
            status=run.status,
            error_message=run.error_message,
            config_snapshot=run.config_snapshot,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
            candidate_rankings=cand_responses,
        )
