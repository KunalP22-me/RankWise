"""Weight recalibration module — updates criterion weights from recruiter overrides using regularized regression."""

import logging
from typing import Any
import numpy as np

logger = logging.getLogger("rankwise.learning.recalibration")


def recalibrate_weights_from_overrides(
    current_weights: dict[str, float],
    candidate_ranking_records: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    regularization_strength: float = 1.5,
) -> dict[str, Any]:
    """Suggest updated criterion weights by fitting Ridge regression on recruiter overrides.

    Uses a Bayesian/Ridge prior centered on current_weights to prevent drastic weight shifts
    with few override samples. Never silently applies changes.
    """
    keys = ["must_have", "nice_to_have", "experience", "education"]
    default_prior = np.array([
        current_weights.get("must_have", 0.40),
        current_weights.get("nice_to_have", 0.20),
        current_weights.get("experience", 0.25),
        current_weights.get("education", 0.15),
    ], dtype=np.float64)

    # If fewer than 2 overrides, return current weights with informative note
    if len(overrides) < 2 or not candidate_ranking_records:
        return {
            "current_weights": current_weights,
            "suggested_weights": current_weights,
            "total_overrides": len(overrides),
            "confidence": 0.20,
            "pattern_summary": "Insufficient override data (minimum 2 overrides required). Current weights maintained.",
        }

    # Map candidate_ranking_id to feature row
    cand_map = {c["id"]: c for c in candidate_ranking_records}

    X_list = []
    y_list = []

    for ov in overrides:
        cr_id = ov.get("candidate_ranking_id")
        cr = cand_map.get(cr_id)
        if not cr:
            continue

        features = [
            float(cr.get("must_have_score", 0.5)),
            float(cr.get("nice_to_have_score", 0.5)),
            float(cr.get("experience_fit_score", 0.5)),
            float(cr.get("education_fit_score", 0.5)),
        ]
        target = float(ov.get("new_score", cr.get("overall_score", 0.5)))
        X_list.append(features)
        y_list.append(target)

    if len(X_list) < 2:
        return {
            "current_weights": current_weights,
            "suggested_weights": current_weights,
            "total_overrides": len(overrides),
            "confidence": 0.25,
            "pattern_summary": "Insufficient aligned candidate records for regression. Current weights maintained.",
        }

    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.float64)

    # Ridge estimation: (X^T X + lambda I)^-1 (X^T y + lambda * prior)
    n_features = len(keys)
    lambda_reg = regularization_strength * len(X)
    XtX = X.T @ X + lambda_reg * np.eye(n_features)
    Xty = X.T @ y + lambda_reg * default_prior

    try:
        new_weights_raw = np.linalg.solve(XtX, Xty)
        # Ensure non-negativity
        new_weights_nonneg = np.maximum(new_weights_raw, 0.05)
        # Normalize sum to 1.0
        new_weights_norm = new_weights_nonneg / np.sum(new_weights_nonneg)
    except Exception as e:
        logger.warning(f"Regression solver failed ({e}); falling back to prior weights.")
        new_weights_norm = default_prior

    suggested = {
        k: round(float(w), 3)
        for k, w in zip(keys, new_weights_norm, strict=False)
    }

    # Generate human-readable pattern summary
    diffs = {k: suggested[k] - current_weights.get(k, 0.0) for k in keys}
    max_increase = max(diffs.items(), key=lambda item: item[1])
    max_decrease = min(diffs.items(), key=lambda item: item[1])

    summary_statements = []
    if max_increase[1] > 0.02:
        summary_statements.append(f"You consistently upweighted '{max_increase[0].replace('_', ' ')}' (+{max_increase[1]*100:.1f}%).")
    if max_decrease[1] < -0.02:
        summary_statements.append(f"Downweighted '{max_decrease[0].replace('_', ' ')}' ({max_decrease[1]*100:.1f}%).")

    if not summary_statements:
        pattern_text = "Override adjustments are balanced across criteria. Minor fine-tuning recommended."
    else:
        pattern_text = " ".join(summary_statements)

    return {
        "current_weights": current_weights,
        "suggested_weights": suggested,
        "total_overrides": len(X_list),
        "confidence": min(0.95, round(0.40 + 0.10 * len(X_list), 2)),
        "pattern_summary": pattern_text,
    }
