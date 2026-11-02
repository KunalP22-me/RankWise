"""Evaluation routes — retrieve benchmark ablation results."""

from fastapi import APIRouter
from app.schemas.evaluation import EvaluationResultResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["Evaluation"])


@router.get("/evaluation/results", response_model=list[EvaluationResultResponse])
def get_evaluation_results():
    """Get evaluation harness ablation results comparing Baseline ATS vs Embeddings vs Full System."""
    service = EvaluationService()
    return service.get_evaluation_results()
