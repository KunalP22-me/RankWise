"""Rankings routes — trigger ranking, get results, status polling."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ranking import RankingRunResponse, RankingStatusResponse
from app.services.ranking_service import RankingService

router = APIRouter(tags=["Rankings"])


def _run_ranking_task(job_id: str, db_factory):
    """Background task runner with dedicated session."""
    with db_factory() as db:
        service = RankingService(db)
        service.execute_ranking(job_id)


@router.post("/jobs/{job_id}/rank", status_code=status.HTTP_202_ACCEPTED, response_model=RankingStatusResponse)
def start_ranking(
    job_id: str,
    background_tasks: BackgroundTasks,
    sync: bool = Query(default=False, description="Run synchronously instead of in background"),
    db: Session = Depends(get_db),
):
    """Start ranking candidates for a job."""
    service = RankingService(db)
    from app.repositories.job_repo import JobRepository
    job = JobRepository(db).get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    if sync:
        run = service.execute_ranking(job_id)
        return RankingStatusResponse(
            id=run.id,
            status=run.status,
            error_message=run.error_message,
        )

    # Create run entry in pending state and queue task
    from app.database import SessionLocal
    run = service.repo.create_run(job_id=job_id, status="pending")
    background_tasks.add_task(service.execute_ranking, job_id)

    return RankingStatusResponse(
        id=run.id,
        status="pending",
    )


@router.get("/jobs/{job_id}/rankings", response_model=RankingRunResponse)
def get_rankings(job_id: str, db: Session = Depends(get_db)):
    """Get the latest completed ranking results for a job."""
    service = RankingService(db)
    result = service.get_rankings(job_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No completed ranking run found for job {job_id}.",
        )
    return result


@router.get("/ranking-runs/{run_id}/status", response_model=RankingStatusResponse)
def get_ranking_status(run_id: str, db: Session = Depends(get_db)):
    """Check progress or status of a ranking run."""
    service = RankingService(db)
    status_resp = service.get_run_status(run_id)
    if not status_resp:
        raise HTTPException(
            status_code=404,
            detail=f"Ranking run {run_id} not found.",
        )
    return status_resp
