"""Bias package — blind redaction, counterfactual testing, adverse impact, and proxy warnings."""

from app.core.bias.adverse_impact import calculate_adverse_impact_ratios
from app.core.bias.blind_redactor import redact_parsed_data, redact_text
from app.core.bias.counterfactual import evaluate_counterfactual_delta, perturb_candidate_profile
from app.core.bias.proxy_detector import detect_proxy_correlations

__all__ = [
    "calculate_adverse_impact_ratios",
    "detect_proxy_correlations",
    "evaluate_counterfactual_delta",
    "perturb_candidate_profile",
    "redact_parsed_data",
    "redact_text",
]
