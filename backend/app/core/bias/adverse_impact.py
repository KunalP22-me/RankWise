"""Adverse impact calculation under the EEOC Four-Fifths (80%) Rule."""

from typing import Any


def calculate_adverse_impact_ratios(
    candidate_records: list[dict[str, Any]],
    top_k_shortlist: int | None = None,
    shortlist_score_threshold: float = 0.65,
) -> dict[str, Any]:
    """Calculate shortlisting rates and four-fifths rule adverse impact ratios across demographic groups.

    Under the EEOC 4/5ths rule, if the selection rate for any group is less than 80% (0.80)
    of the selection rate for the group with the highest rate, adverse impact is indicated.
    """
    if not candidate_records:
        return {
            "four_fifths_violation": False,
            "groups": {},
            "summary": "No candidate records available for adverse impact calculation.",
        }

    # If top_k_shortlist not specified, shortlist top 33% or threshold
    total_candidates = len(candidate_records)
    k = top_k_shortlist or max(1, total_candidates // 3)

    # Sort by rank or score
    sorted_candidates = sorted(
        candidate_records,
        key=lambda x: x.get("rank", 9999),
    )

    # Classify group (use explicit group or heuristic infer from name/pronouns)
    group_counts: dict[str, int] = {}
    group_shortlisted: dict[str, int] = {}

    for idx, c in enumerate(sorted_candidates):
        group = c.get("group")
        if not group:
            # Heuristic grouping for audit (Cohort A / Cohort B or inferred gender)
            text = (c.get("raw_text") or "").lower()
            if "she" in text or "her" in text or "ms." in text:
                group = "Female Inferred"
            elif "he" in text or "him" in text or "mr." in text:
                group = "Male Inferred"
            else:
                group = "Non-Specified / Neutral"

        group_counts[group] = group_counts.get(group, 0) + 1

        is_shortlisted = (idx < k) or (c.get("overall_score", 0.0) >= shortlist_score_threshold)
        if is_shortlisted:
            group_shortlisted[group] = group_shortlisted.get(group, 0) + 1
        else:
            group_shortlisted.setdefault(group, 0)

    # Compute selection rates
    selection_rates: dict[str, float] = {}
    for g, total in group_counts.items():
        sl = group_shortlisted.get(g, 0)
        selection_rates[g] = round(sl / total, 4)

    max_rate = max(selection_rates.values()) if selection_rates else 1.0
    ratios: dict[str, float] = {}
    violation_flag = False
    groups_summary: dict[str, Any] = {}

    for g, rate in selection_rates.items():
        ratio = round(rate / max_rate, 4) if max_rate > 0 else 1.0
        ratios[g] = ratio
        is_sub_80 = ratio < 0.80 and group_counts[g] >= 2
        if is_sub_80:
            violation_flag = True

        groups_summary[g] = {
            "total_applicants": group_counts[g],
            "shortlisted": group_shortlisted[g],
            "selection_rate": rate,
            "impact_ratio": ratio,
            "adverse_impact_flag": is_sub_80,
        }

    return {
        "four_fifths_violation": violation_flag,
        "max_selection_rate": max_rate,
        "groups": groups_summary,
        "summary": (
            "Adverse impact detected: one or more demographic groups have shortlisting rates below 80% of the baseline group."
            if violation_flag
            else "Complies with Four-Fifths (80%) Rule. No adverse impact detected across demographic cohorts."
        ),
    }
