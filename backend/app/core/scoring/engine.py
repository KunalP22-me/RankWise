"""Deterministic Scoring Engine — transparent formula where LLM never sets the final numeric score."""

import re
from typing import Any


def compute_evidence_location_weight(chunk_type: str) -> float:
    """Weight evidence location: experience bullet > project > skills list > summary/education."""
    weights = {
        "experience": 1.0,
        "project": 0.85,
        "skill": 0.60,
        "summary": 0.50,
        "education": 0.40,
    }
    return weights.get(chunk_type, 0.50)


def compute_recency_weight(chunk_metadata: dict[str, Any]) -> float:
    """Compute recency weight based on role end_date."""
    end_date = str(chunk_metadata.get("end_date", "")).lower()
    if not end_date:
        return 0.80  # Default neutral recency

    if "present" in end_date or "current" in end_date or "now" in end_date:
        return 1.0

    match = re.search(r"\b(20\d{2})\b", end_date)
    if match:
        year = int(match.group(1))
        diff = max(0, 2026 - year)
        if diff <= 2:
            return 1.0
        elif diff <= 4:
            return 0.85
        elif diff <= 6:
            return 0.70
        else:
            return 0.55
    return 0.80


def compute_duration_weight(total_experience_years: float) -> float:
    """Weight for overall candidate experience depth."""
    if total_experience_years >= 5:
        return 1.0
    elif total_experience_years >= 3:
        return 0.85
    elif total_experience_years >= 1:
        return 0.70
    return 0.50


def compute_requirement_score(
    verdict: str,
    semantic_similarity: float,
    location_weight: float,
    recency_weight: float,
    duration_weight: float = 1.0,
) -> float:
    """Compute individual requirement score deterministically in code.

    LLM verdict provides the categorical qualifier:
      - 'Strong': 1.0
      - 'Partial': 0.55
      - 'None': 0.0 (Strictly zeroes out the requirement score)

    Combined formula:
      Score = verdict_multiplier * (0.45 * similarity + 0.30 * location + 0.15 * recency + 0.10 * duration)
    """
    verdict_multipliers = {
        "Strong": 1.0,
        "Partial": 0.55,
        "None": 0.0,
    }
    multiplier = verdict_multipliers.get(verdict, 0.0)
    if multiplier == 0.0:
        return 0.0

    raw_score = (
        0.45 * max(0.0, min(1.0, semantic_similarity))
        + 0.30 * location_weight
        + 0.15 * recency_weight
        + 0.10 * duration_weight
    )
    final_score = multiplier * max(0.0, min(1.0, raw_score))
    return round(final_score, 4)


def compute_experience_fit(candidate_years: float, required_years: float | None) -> float:
    """Compute experience fit score against required years."""
    if required_years is None or required_years <= 0:
        return 1.0
    if candidate_years >= required_years:
        return 1.0
    return round(max(0.0, candidate_years / required_years), 4)


def compute_education_fit(
    candidate_education: list[dict],
    required_education: str | None,
) -> float:
    """Deterministic education fit scoring based on degree hierarchy."""
    if not required_education or required_education.strip().lower() in ("any", "none", "not required", ""):
        return 1.0

    req_lower = required_education.lower()
    degree_levels = {
        "phd": 5,
        "doctor": 5,
        "master": 4,
        "m.s": 4,
        "m.tech": 4,
        "bachelor": 3,
        "b.s": 3,
        "b.e": 3,
        "b.tech": 3,
        "associate": 2,
        "diploma": 2,
        "high school": 1,
    }

    req_level = 3  # Default bachelor
    for k, v in degree_levels.items():
        if k in req_lower:
            req_level = v
            break

    cand_level = 0
    for edu in candidate_education:
        text = (str(edu.get("degree", "")) + " " + str(edu.get("institution", ""))).lower()
        for k, v in degree_levels.items():
            if k in text:
                cand_level = max(cand_level, v)

    if cand_level == 0:
        cand_level = 2  # Baseline if education listed

    if cand_level >= req_level:
        return 1.0
    elif cand_level == req_level - 1:
        return 0.75
    else:
        return 0.50


def compute_overall_score(
    must_have_score: float,
    nice_to_have_score: float,
    experience_fit_score: float,
    education_fit_score: float,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute weighted overall score (0.0 - 1.0) using configurable job weights."""
    default_weights = {
        "must_have": 0.40,
        "nice_to_have": 0.20,
        "experience": 0.25,
        "education": 0.15,
    }
    w = weights or default_weights
    total_w = sum(w.values()) or 1.0

    score = (
        (w.get("must_have", 0.40) * must_have_score)
        + (w.get("nice_to_have", 0.20) * nice_to_have_score)
        + (w.get("experience", 0.25) * experience_fit_score)
        + (w.get("education", 0.15) * education_fit_score)
    ) / total_w

    return round(max(0.0, min(1.0, score)), 4)
