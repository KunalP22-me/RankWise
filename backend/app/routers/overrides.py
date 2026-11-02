"""Overrides routes — score overrides and learned weight adjustments."""

from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.override import OverrideCreate, OverrideResponse, WeightSuggestionResponse
from app.services.override_service import OverrideService

router = APIRouter(tags=["Overrides"])


@router.post("/rankings/{ranking_id}/override", response_model=OverrideResponse, status_code=status.HTTP_201_CREATED)
def create_override(
    ranking_id: str,
    override_data: OverrideCreate,
    db: Session = Depends(get_db),
):
    """Create a score override for a candidate ranking."""
    service = OverrideService(db)
    try:
        return service.create_override(ranking_id, override_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/weight-suggestions", response_model=WeightSuggestionResponse)
def get_weight_suggestions(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get learned criterion weight suggestions derived from recruiter overrides."""
    service = OverrideService(db)
    try:
        return service.get_weight_suggestions(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/jobs/{job_id}/weight-suggestions/accept")
def accept_weight_suggestions(
    job_id: str,
    weights_payload: dict[str, float] = Body(..., embed=True, alias="weights"),
    db: Session = Depends(get_db),
):
    """Accept and persist recruiter-approved weight changes."""
    service = OverrideService(db)
    try:
        return service.accept_weight_suggestions(job_id, weights_payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
