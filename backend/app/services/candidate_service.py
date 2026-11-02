"""Candidate service — business logic for candidate management and uploads."""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.parser import ResumeParserPipeline
from app.repositories.candidate_repo import CandidateRepository
from app.schemas.candidate import CandidateResponse

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class CandidateService:
    """Business logic for candidates."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CandidateRepository(db)

    def get_candidate(self, candidate_id: str) -> CandidateResponse | None:
        """Get a candidate by ID."""
        c = self.repo.get_by_id(candidate_id)
        if not c:
            return None
        return CandidateResponse.model_validate(c)

    def get_candidates_by_job(self, job_id: str) -> list[CandidateResponse]:
        """Get all candidates for a job."""
        candidates = self.repo.get_by_job(job_id)
        return [CandidateResponse.model_validate(c) for c in candidates]

    async def upload_resume(
        self, job_id: str, file: UploadFile
    ) -> CandidateResponse:
        """Upload and store a single resume file."""
        # Validate file type
        ext = Path(file.filename).suffix.lower() if file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

        file_type = "pdf" if ext == ".pdf" else "docx"

        # Validate file size
        content = await file.read()
        if len(content) > settings.max_file_size_bytes:
            raise ValueError(
                f"File too large: {len(content)} bytes. Max: {settings.max_file_size_mb} MB"
            )

        # Save file
        file_id = str(uuid.uuid4())
        save_dir = settings.upload_path / job_id
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / f"{file_id}{ext}"
        file_path.write_bytes(content)

        # Parse resume content using hybrid pipeline
        parser = ResumeParserPipeline(db=self.db)
        parse_res = parser.parse_file(file_path)

        # Create DB entry with parsed metadata
        candidate = self.repo.create(
            job_id=job_id,
            filename=file.filename or f"resume{ext}",
            file_path=str(file_path),
            file_type=file_type,
            status="parsed" if parse_res.get("parse_confidence", 0) > 0 else "uploaded",
            raw_text=parse_res.get("raw_text"),
            parsed_data=parse_res.get("parsed_data"),
            parse_method=parse_res.get("parse_method"),
            parse_confidence=parse_res.get("parse_confidence"),
            parse_warnings=parse_res.get("parse_warnings"),
            total_experience_years=parse_res.get("total_experience_years"),
        )
        return CandidateResponse.model_validate(candidate)

    async def upload_bulk(
        self, job_id: str, files: list[UploadFile]
    ) -> list[CandidateResponse]:
        """Upload multiple resume files."""
        results = []
        for f in files:
            try:
                result = await self.upload_resume(job_id, f)
                results.append(result)
            except ValueError:
                # Skip invalid files but continue processing
                continue
        return results

    def delete_candidate(self, candidate_id: str) -> bool:
        """Delete a candidate and their file."""
        c = self.repo.get_by_id(candidate_id)
        if not c:
            return False
        # Remove file
        try:
            if os.path.exists(c.file_path):
                os.remove(c.file_path)
        except OSError:
            pass
        return self.repo.delete(candidate_id)
