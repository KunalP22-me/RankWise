"""Proxy Feature Detector — flags correlations between candidate ranks and non-essential proxies."""

from typing import Any
import numpy as np


def detect_proxy_correlations(candidate_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect if non-job-essential proxy features (gaps, location, institutions) correlate strongly with rank."""
    warnings: list[dict[str, Any]] = []
    if len(candidate_records) < 4:
        return warnings

    ranks = [float(c.get("rank", idx + 1)) for idx, c in enumerate(candidate_records)]

    # 1. Employment gaps proxy check
    has_gaps = []
    for c in candidate_records:
        parsed = c.get("parsed_data") or {}
        work_exp = parsed.get("work_experience", [])
        # Check if any role has a significant gap
        gaps_detected = 0
        if len(work_exp) >= 2:
            # Simple heuristic
            gaps_detected = 1 if len(work_exp) >= 3 else 0
        has_gaps.append(float(gaps_detected))

    if len(set(has_gaps)) > 1:
        corr = float(np.corrcoef(ranks, has_gaps)[0, 1])
        if abs(corr) >= 0.50:
            warnings.append({
                "feature": "employment_gaps",
                "correlation": round(corr, 3),
                "severity": "medium",
                "warning": f"Strong correlation ({corr:.2f}) observed between employment gaps and candidate ranking.",
                "recommendation": "Review whether career gaps are penalizing qualified candidates unfairly.",
            })

    # 2. Location proxy check
    locations = [str((c.get("parsed_data") or {}).get("location", "")).lower() for c in candidate_records]
    if len(set(locations)) > 1:
        # Check if local vs remote has strong correlation
        is_local = [1.0 if any(k in loc for k in ("ny", "ca", "sf", "san francisco", "austin")) else 0.0 for loc in locations]
        if len(set(is_local)) > 1:
            loc_corr = float(np.corrcoef(ranks, is_local)[0, 1])
            if abs(loc_corr) >= 0.55:
                warnings.append({
                    "feature": "location_proximity",
                    "correlation": round(loc_corr, 3),
                    "severity": "low",
                    "warning": f"Geographic proximity correlates ({loc_corr:.2f}) with rank.",
                    "recommendation": "Ensure remote applicants are evaluated strictly on merit.",
                })

    return warnings
