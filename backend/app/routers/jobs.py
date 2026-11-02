"""Job routes — CRUD, requirements extraction, and JD bias check."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(data: JobCreate, db: Session = Depends(get_db)):
    """Create a new job posting."""
    svc = JobService(db)
    return svc.create_job(data)


@router.get("", response_model=list[JobResponse])
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all jobs."""
    svc = JobService(db)
    return svc.list_jobs(skip=skip, limit=limit)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get a job by ID."""
    svc = JobService(db)
    job = svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: str, data: JobUpdate, db: Session = Depends(get_db)):
    """Update a job."""
    svc = JobService(db)
    job = svc.update_job(job_id, data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job."""
    svc = JobService(db)
    if not svc.delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("/{job_id}/extract-requirements")
def extract_requirements(job_id: str, db: Session = Depends(get_db)):
    """Extract structured requirements from JD using LLM."""
    svc = JobService(db)
    result = svc.extract_requirements(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.post("/{job_id}/jd-bias-check")
def jd_bias_check(job_id: str, db: Session = Depends(get_db)):
    """Check JD for biased wording."""
    svc = JobService(db)
    result = svc.check_bias(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.get("/{job_id}/audit-log")
def get_job_audit_log(job_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get audit logs for a specific job."""
    from app.repositories.audit_repo import AuditRepository
    repo = AuditRepository(db)
    logs = repo.get_by_job(job_id, skip=skip, limit=limit)
    return [
        {
            "id": l.id,
            "action": l.action,
            "job_id": l.job_id,
            "user": l.user,
            "detail": l.detail,
            "llm_provider": l.llm_provider,
            "llm_model": l.llm_model,
            "latency_ms": l.latency_ms,
            "token_count": l.token_count,
            "created_at": l.created_at,
        }
        for l in logs
    ]


@router.get("/all/audit-logs")
def get_all_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all audit logs across all jobs."""
    from app.repositories.audit_repo import AuditRepository
    repo = AuditRepository(db)
    logs = repo.get_all(skip=skip, limit=limit)
    return [
        {
            "id": l.id,
            "action": l.action,
            "job_id": l.job_id,
            "user": l.user,
            "detail": l.detail,
            "llm_provider": l.llm_provider,
            "llm_model": l.llm_model,
            "latency_ms": l.latency_ms,
            "token_count": l.token_count,
            "created_at": l.created_at,
        }
        for l in logs
    ]

