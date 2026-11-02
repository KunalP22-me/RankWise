"""Evidence judging module — calls LLM to judge evidence snippets against requirements."""

import logging
from app.core.llm import LLMClient, render_prompt
from app.schemas.llm import LLMEvidenceVerdict

logger = logging.getLogger("rankwise.scoring.judge")


def judge_evidence(
    requirement_text: str,
    snippets: list[str],
    llm: LLMClient,
) -> LLMEvidenceVerdict:
    """Evaluate whether candidate snippets satisfy a specific job requirement."""
    if not snippets or all(not s.strip() for s in snippets):
        return LLMEvidenceVerdict(
            verdict="None",
            reason="No relevant evidence snippets found in candidate resume.",
        )

    snippets_text = "\n---\n".join(f"[{i+1}] {s.strip()}" for i, s in enumerate(snippets) if s.strip())

    try:
        prompt = render_prompt(
            "v1_evidence_judging.txt",
            requirement_text=requirement_text,
            snippets_text=snippets_text,
        )
        verdict_obj: LLMEvidenceVerdict = llm.generate_structured(
            prompt, LLMEvidenceVerdict, temperature=0.0
        )
        return verdict_obj
    except Exception as e:
        logger.warning(f"Evidence judging LLM call failed ({e}). Using conservative fallback.")
        # Rule-based fallback if LLM is unavailable
        req_lower = requirement_text.lower()
        combined_text = snippets_text.lower()
        words = [w for w in req_lower.split() if len(w) > 3]
        matches = sum(1 for w in words if w in combined_text)
        ratio = matches / max(1, len(words))

        if ratio >= 0.5:
            return LLMEvidenceVerdict(
                verdict="Partial",
                reason=f"Candidate resume mentions key related terminology ({matches}/{len(words)} terms).",
            )
        return LLMEvidenceVerdict(
            verdict="None",
            reason="Insufficient evidence found in candidate resume.",
        )
