"""Candidate routes — upload, list, get, delete."""


from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.candidate import CandidateResponse
from app.services.candidate_service import CandidateService

router = APIRouter(tags=["Candidates"])


@router.post(
    "/jobs/{job_id}/candidates",
    response_model=list[CandidateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_candidates(
    job_id: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload one or more resume files (PDF/DOCX) for a job."""
    svc = CandidateService(db)
    try:
        results = await svc.upload_bulk(job_id, files)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not results:
        raise HTTPException(status_code=400, detail="No valid files uploaded")
    return results


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateResponse])
def list_candidates(job_id: str, db: Session = Depends(get_db)):
    """List all candidates for a job."""
    svc = CandidateService(db)
    return svc.get_candidates_by_job(job_id)


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Get a candidate by ID."""
    svc = CandidateService(db)
    candidate = svc.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Delete a candidate."""
    svc = CandidateService(db)
    if not svc.delete_candidate(candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
