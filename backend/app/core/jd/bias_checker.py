"""Job description bias, ageism, and exclusionary wording checker."""

import logging
import re
from sqlalchemy.orm import Session

from app.core.llm import get_llm_client, render_prompt
from app.schemas.job import BiasFlag, JDBiasCheckResult

logger = logging.getLogger("rankwise.jd.bias")

# Curated catalog of known exclusionary phrases and neutral alternatives
KNOWN_BIAS_CATALOG = [
    {
        "pattern": r"\b(?:young\b|youthful\b|recent college grad(?:uate)?s?\s+only)\b",
        "issue": "Age-exclusionary language that discriminates against experienced workers (ADEA risk).",
        "suggestion": "motivated professional or qualified candidate",
        "severity": "high",
    },
    {
        "pattern": r"\b(?:digital native|digital natives)\b",
        "issue": "Age-exclusionary proxy term strongly associated with age bias.",
        "suggestion": "proficient with modern digital tools and software",
        "severity": "high",
    },
    {
        "pattern": r"\b(?:rockstar|ninja|guru|wizard|hacker)\b",
        "issue": "Masculine-coded jargon that lowers application rates among female and diverse engineers.",
        "suggestion": "accomplished or high-performing software engineer",
        "severity": "medium",
    },
    {
        "pattern": r"\b(?:he/him|he will|his responsibility)\b",
        "issue": "Gendered pronoun assumption in general job responsibilities.",
        "suggestion": "they/them or 'the candidate'",
        "severity": "medium",
    },
    {
        "pattern": r"\b(?:aggressive|killer instinct|crush it|work hard,? play hard)\b",
        "issue": "Hyper-competitive masculine phrasing that detracts from inclusive team culture.",
        "suggestion": "results-driven, proactive, and collaborative",
        "severity": "low",
    },
]


def check_jd_bias(jd_text: str, db: Session | None = None) -> JDBiasCheckResult:
    """Analyze job description for exclusionary bias using rule heuristics and LLM evaluation."""
    flags: list[BiasFlag] = []

    # 1. Rule-based catalog pass
    for item in KNOWN_BIAS_CATALOG:
        match = re.search(item["pattern"], jd_text, re.IGNORECASE)
        if match:
            flags.append(
                BiasFlag(
                    original_text=match.group(0),
                    issue=item["issue"],
                    suggestion=item["suggestion"],
                    severity=item["severity"],
                )
            )

    # 2. LLM contextual bias pass
    try:
        llm = get_llm_client(db=db)
        prompt = render_prompt("v1_jd_bias_check.txt", jd_text=jd_text)
        llm_result: JDBiasCheckResult = llm.generate_structured(
            prompt, JDBiasCheckResult, temperature=0.0
        )
        # Deduplicate and combine flags
        seen_texts = {f.original_text.lower() for f in flags}
        for f in llm_result.flags:
            if f.original_text.lower() not in seen_texts:
                flags.append(f)
                seen_texts.add(f.original_text.lower())
    except Exception as e:
        logger.warning(f"LLM JD bias check failed: {e}. Falling back to rule catalog.")

    is_clean = len(flags) == 0
    assessment = (
        "No exclusionary wording or demographic bias detected. Job posting adheres to DEI best practices."
        if is_clean
        else f"Detected {len(flags)} potentially exclusionary or biased phrasing issues."
    )

    return JDBiasCheckResult(
        flags=flags,
        overall_assessment=assessment,
        is_clean=is_clean,
    )
