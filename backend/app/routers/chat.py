"""Chat routes — recruiter assistant Q&A with evidence citations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(tags=["Chat"])


@router.post("/jobs/{job_id}/chat", response_model=ChatResponse)
def chat_with_assistant(
    job_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
):
    """Ask recruiter questions about the candidate pool with grounded citations."""
    service = ChatService(db)
    try:
        return service.answer_query(job_id=job_id, question=payload.question)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
