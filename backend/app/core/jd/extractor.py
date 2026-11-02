"""LLM-driven job description structured requirements extraction."""

import logging
from sqlalchemy.orm import Session

from app.core.jd.ontology import ontology
from app.core.llm import get_llm_client, render_prompt
from app.schemas.job import JobRequirements

logger = logging.getLogger("rankwise.jd.extractor")


def extract_job_requirements(jd_text: str, db: Session | None = None) -> JobRequirements:
    """Extract structured requirements, must-haves, nice-to-haves, and implied skills from a JD."""
    llm = get_llm_client(db=db)
    prompt = render_prompt("v1_jd_extraction.txt", jd_text=jd_text)

    try:
        reqs = llm.generate_structured(prompt, JobRequirements, temperature=0.0)
    except Exception as e:
        logger.error(f"Failed to extract structured requirements via LLM: {e}")
        # Deterministic fallback
        reqs = JobRequirements(
            must_have=[],
            nice_to_have=[],
            minimum_experience_years=None,
            seniority_level=None,
            education_requirement=None,
            responsibilities=[],
            implied_skills=[],
        )

    # Enrich implied skills using ontology
    enriched_implied = set(reqs.implied_skills)
    for req in reqs.must_have + reqs.nice_to_have:
        for s in req.implied_skills:
            enriched_implied.add(s)
            parent = ontology.get_parent(s)
            if parent:
                enriched_implied.add(parent.title())

    reqs.implied_skills = sorted(list(enriched_implied))
    return reqs
