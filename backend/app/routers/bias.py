"""Bias routes — bias reports and counterfactual fairness testing."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.bias import BiasReportResponse
from app.services.bias_service import BiasService

router = APIRouter(tags=["Bias"])


@router.get("/jobs/{job_id}/bias-report", response_model=BiasReportResponse)
def get_bias_report(job_id: str, db: Session = Depends(get_db)):
    """Get bias audit report for the latest ranking run of a job."""
    service = BiasService(db)
    report = service.get_bias_report_for_job(job_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No completed ranking run or bias report found for job {job_id}.",
        )
    return report


@router.post("/jobs/{job_id}/counterfactual-test")
def run_counterfactual_test(job_id: str, db: Session = Depends(get_db)):
    """Run counterfactual perturbation testing for a job's candidate pool."""
    service = BiasService(db)
    try:
        results = service.run_counterfactual_test_for_job(job_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
