"""Hybrid Resume Parsing Pipeline (Rules + LLM Fallback + Confidence Scoring)."""

import logging
from pathlib import Path
from sqlalchemy.orm import Session

from app.config import settings
from app.core.llm import get_llm_client, render_prompt
from app.core.parser.date_calculator import calculate_experience_years
from app.core.parser.docx_parser import extract_text_from_docx
from app.core.parser.pdf_parser import extract_text_from_pdf
from app.core.parser.section_heuristics import (
    extract_contact_info,
    extract_skills_from_text,
    parse_education,
    parse_work_experience,
    split_into_sections,
)
from app.schemas.candidate import Education, Project, ResumeData, WorkExperience
from app.schemas.llm import LLMResumeExtraction

logger = logging.getLogger("rankwise.parser.pipeline")


def compute_parse_confidence(data: dict) -> float:
    """Calculate rule-based parse confidence score based on entity completeness (0.0 - 1.0)."""
    score = 0.0
    if data.get("name"):
        score += 0.20
    if data.get("email") or data.get("phone"):
        score += 0.20
    if data.get("work_experience") and len(data["work_experience"]) > 0:
        score += 0.25
    if data.get("skills") and len(data["skills"]) >= 2:
        score += 0.20
    if data.get("education") and len(data["education"]) > 0:
        score += 0.15
    return round(min(1.0, score), 2)


class ResumeParserPipeline:
    """Hybrid pipeline for parsing resumes with rule-based heuristics and LLM fallback."""

    def __init__(self, db: Session | None = None):
        self.db = db

    def parse_file(self, file_path: str | Path) -> dict:
        """Parse resume file from disk.

        Returns dictionary with:
        - raw_text: str
        - parsed_data: dict
        - parse_method: "rules" | "llm_fallback" | "failed"
        - parse_confidence: float
        - parse_warnings: list[str]
        - total_experience_years: float
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        # Step 1: Raw text extraction
        if ext == ".pdf":
            raw_text, warnings = extract_text_from_pdf(path)
        elif ext == ".docx":
            raw_text, warnings = extract_text_from_docx(path)
        else:
            return {
                "raw_text": "",
                "parsed_data": {},
                "parse_method": "failed",
                "parse_confidence": 0.0,
                "parse_warnings": [f"Unsupported file extension: {ext}"],
                "total_experience_years": 0.0,
            }

        if not raw_text.strip():
            return {
                "raw_text": raw_text,
                "parsed_data": {},
                "parse_method": "failed",
                "parse_confidence": 0.0,
                "parse_warnings": warnings or ["No readable text found in document."],
                "total_experience_years": 0.0,
            }

        # Step 2: Rule-based heuristic extraction
        sections = split_into_sections(raw_text)
        contact = extract_contact_info(raw_text)
        skills = extract_skills_from_text(sections.get("skills", ""), raw_text)
        work_exp = parse_work_experience(sections.get("experience", ""))
        education = parse_education(sections.get("education", ""))

        rule_data = {
            "name": contact["name"],
            "email": contact["email"],
            "phone": contact["phone"],
            "location": contact["location"],
            "summary": sections.get("summary") or None,
            "skills": skills,
            "work_experience": work_exp,
            "projects": [],
            "education": education,
            "certifications": [c.strip() for c in sections.get("certifications", "").split("\n") if c.strip()],
        }

        confidence = compute_parse_confidence(rule_data)
        parse_method = "rules"

        # Step 3: LLM Fallback if confidence is below threshold
        if confidence < settings.parse_confidence_threshold and len(raw_text.strip()) > 30:
            logger.info(
                f"Parse confidence ({confidence:.2f}) below threshold ({settings.parse_confidence_threshold}). "
                f"Invoking LLM fallback parser."
            )
            try:
                llm = get_llm_client(db=self.db)
                prompt = render_prompt("v1_resume_extraction.txt", resume_text=raw_text)
                extracted_llm: LLMResumeExtraction = llm.generate_structured(
                    prompt, LLMResumeExtraction, temperature=0.0
                )

                # Merge / replace with LLM results
                rule_data["name"] = extracted_llm.name or rule_data["name"]
                rule_data["email"] = extracted_llm.email or rule_data["email"]
                rule_data["phone"] = extracted_llm.phone or rule_data["phone"]
                rule_data["location"] = extracted_llm.location or rule_data["location"]
                rule_data["summary"] = extracted_llm.summary or rule_data["summary"]
                if extracted_llm.skills:
                    rule_data["skills"] = list(set(rule_data["skills"] + extracted_llm.skills))
                if extracted_llm.work_experience:
                    rule_data["work_experience"] = extracted_llm.work_experience
                if extracted_llm.projects:
                    rule_data["projects"] = extracted_llm.projects
                if extracted_llm.education:
                    rule_data["education"] = extracted_llm.education
                if extracted_llm.certifications:
                    rule_data["certifications"] = list(set(rule_data["certifications"] + extracted_llm.certifications))

                parse_method = "llm_fallback"
                confidence = max(0.85, compute_parse_confidence(rule_data))

            except Exception as e:
                logger.error(f"LLM fallback parser failed: {e}")
                warnings.append(f"llm_fallback_error: {str(e)}")

        # Step 4: Calculate total experience years
        total_exp = calculate_experience_years(rule_data["work_experience"])

        return {
            "raw_text": raw_text,
            "parsed_data": rule_data,
            "parse_method": parse_method,
            "parse_confidence": confidence,
            "parse_warnings": warnings,
            "total_experience_years": total_exp,
        }
