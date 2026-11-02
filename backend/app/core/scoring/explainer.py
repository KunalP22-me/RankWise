"""Candidate explanation module — generates grounded strengths, gaps, and interview questions."""

import logging
from app.core.llm import LLMClient, render_prompt
from app.schemas.llm import LLMCandidateExplanation

logger = logging.getLogger("rankwise.scoring.explainer")


def generate_candidate_explanation(
    job_title: str,
    requirement_verdicts: list[dict],
    candidate_evidence: str,
    llm: LLMClient,
) -> LLMCandidateExplanation:
    """Generate grounded recruiter explanation summarizing strengths, gaps, and targeted interview questions."""
    verdicts_summary = "\n".join(
        f"- Requirement: {v.get('requirement_text', '')} | Verdict: {v.get('verdict', 'None')} | Reason: {v.get('verdict_reason', '')}"
        for v in requirement_verdicts
    )

    try:
        prompt = render_prompt(
            "v1_candidate_explanation.txt",
            job_title=job_title,
            verdicts_summary=verdicts_summary,
            candidate_evidence=candidate_evidence[:3000],  # Bound context window
        )
        explanation: LLMCandidateExplanation = llm.generate_structured(
            prompt, LLMCandidateExplanation, temperature=0.0
        )
        return explanation
    except Exception as e:
        logger.warning(f"Candidate explanation LLM generation failed ({e}). Producing deterministic summary.")
        strengths = []
        gaps = []
        for v in requirement_verdicts:
            req_text = v.get("requirement_text", "")
            verdict = v.get("verdict", "")
            if verdict == "Strong":
                strengths.append(f"Demonstrated proficiency in {req_text}.")
            elif verdict == "None":
                gaps.append(f"Missing documented experience in {req_text}.")

        interview_questions = [
            f"Can you explain your direct experience working with {g.replace('Missing documented experience in ', '').rstrip('.')} in production?",
            "How do your past technical projects prepare you for this role's architecture challenges?",
            "What technical trade-offs have you managed when scaling distributed systems?",
        ]

        summary_text = (
            f"Candidate evaluated for {job_title}. Identified {len(strengths)} confirmed strength(s) "
            f"and {len(gaps)} potential technical gap(s) against required criteria."
        )

        return LLMCandidateExplanation(
            strengths=strengths[:5] or ["Demonstrated relevant technical background."],
            gaps=gaps[:5] or ["No critical requirement gaps flagged."],
            interview_questions=interview_questions[:3],
            summary=summary_text,
        )
