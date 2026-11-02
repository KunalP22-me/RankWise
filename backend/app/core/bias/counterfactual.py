"""Counterfactual Perturbation Module — swaps protected demographic signals and audits score stability."""

import re
from typing import Any
from app.core.scoring.engine import compute_overall_score

# Canonical test pairs for gender/demographic counterfactuals
NAME_SWAP_PAIRS = [
    ("Michael", "Sarah"),
    ("David", "Emily"),
    ("James", "Priya"),
    ("Robert", "Jessica"),
    ("John", "Aaliyah"),
    ("Christopher", "Mei"),
]

PRONOUN_SWAPS = {
    r"\bhe\b": "she",
    r"\bhim\b": "her",
    r"\bhis\b": "her",
    r"\bhimself\b": "herself",
}

REVERSE_PRONOUN_SWAPS = {
    r"\bshe\b": "he",
    r"\bher\b": "him",
    r"\bhers\b": "his",
    r"\bherself\b": "himself",
}


def perturb_candidate_profile(
    candidate_name: str,
    raw_text: str,
    parsed_data: dict[str, Any],
) -> tuple[str, str, dict[str, Any], list[str]]:
    """Generate a counterfactual perturbed candidate profile with swapped demographic signals."""
    swaps_applied = []
    perturbed_name = candidate_name
    perturbed_text = raw_text or ""
    perturbed_parsed = dict(parsed_data)

    # 1. Swap name
    found_name_pair = False
    for m_name, f_name in NAME_SWAP_PAIRS:
        if m_name.lower() in candidate_name.lower():
            perturbed_name = re.sub(re.escape(m_name), f_name, candidate_name, flags=re.IGNORECASE)
            perturbed_text = re.sub(re.escape(m_name), f_name, perturbed_text, flags=re.IGNORECASE)
            swaps_applied.append(f"Name swapped: {m_name} -> {f_name}")
            found_name_pair = True
            break
        elif f_name.lower() in candidate_name.lower():
            perturbed_name = re.sub(re.escape(f_name), m_name, candidate_name, flags=re.IGNORECASE)
            perturbed_text = re.sub(re.escape(f_name), m_name, perturbed_text, flags=re.IGNORECASE)
            swaps_applied.append(f"Name swapped: {f_name} -> {m_name}")
            found_name_pair = True
            break

    if not found_name_pair:
        # Default name swap
        first_token = candidate_name.split()[0] if candidate_name else "Candidate"
        perturbed_name = f"Taylor (Variant of {first_token})"
        swaps_applied.append("Name generalized to neutral variant: Taylor")

    # 2. Swap pronouns
    pronoun_detected = False
    for pat, rep in PRONOUN_SWAPS.items():
        if re.search(pat, perturbed_text, flags=re.IGNORECASE):
            perturbed_text = re.sub(pat, rep, perturbed_text, flags=re.IGNORECASE)
            pronoun_detected = True

    if not pronoun_detected:
        for pat, rep in REVERSE_PRONOUN_SWAPS.items():
            if re.search(pat, perturbed_text, flags=re.IGNORECASE):
                perturbed_text = re.sub(pat, rep, perturbed_text, flags=re.IGNORECASE)

    swaps_applied.append("Pronoun gender alignment inverted")
    perturbed_parsed["name"] = perturbed_name

    return perturbed_name, perturbed_text, perturbed_parsed, swaps_applied


def evaluate_counterfactual_delta(
    original_score: float,
    perturbed_score: float,
    delta_threshold: float = 0.05,
) -> dict[str, Any]:
    """Calculate score delta between original candidate and counterfactual variant."""
    delta = abs(original_score - perturbed_score)
    is_flagged = delta > delta_threshold
    return {
        "original_score": round(original_score, 4),
        "perturbed_score": round(perturbed_score, 4),
        "score_delta": round(delta, 4),
        "threshold": delta_threshold,
        "is_flagged": is_flagged,
    }
