"""Blind Mode Redaction Module — redacts PII and protected attributes before scoring and LLM calls."""

import re
from typing import Any

# Pronoun mapping for gender-neutral redaction
PRONOUN_MAP = {
    r"\bhe\b": "they",
    r"\bshe\b": "they",
    r"\bhim\b": "them",
    r"\bher\b": "them",
    r"\bhis\b": "their",
    r"\bhers\b": "theirs",
    r"\bhimself\b": "themselves",
    r"\bherself\b": "themselves",
    r"\bmr\.\b": "Mx.",
    r"\bmrs\.\b": "Mx.",
    r"\bms\.\b": "Mx.",
}

# Common graduation / birth year patterns: "Class of 1998", "Graduated 2001", "DOB: 1985"
AGE_PATTERNS = [
    r"\b(?:class of|graduated in|graduated)\s+(?:19|20)\d{2}\b",
    r"\b(?:dob|birth|born)[:\s]+(?:\d{1,2}[/-])?\d{1,2}[/-](?:19|20)\d{2}\b",
    r"\b\d{1,2}\s+years\s+old\b",
]


def redact_text(
    text: str,
    candidate_name: str | None = None,
    candidate_email: str | None = None,
    candidate_phone: str | None = None,
    redact_institutions: bool = False,
    institutions: list[str] | None = None,
) -> str:
    """Redact identifiable protected signals from raw resume text."""
    if not text:
        return ""

    redacted = text

    # 1. Redact email first (prevents name tokens inside email from breaking email regex)
    if candidate_email:
        redacted = re.sub(re.escape(candidate_email), "[REDACTED_EMAIL]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", redacted)

    # 2. Redact phone numbers
    if candidate_phone:
        redacted = re.sub(re.escape(candidate_phone), "[REDACTED_PHONE]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[REDACTED_PHONE]", redacted)

    # 3. Redact candidate name tokens
    if candidate_name and len(candidate_name.strip()) > 2:
        for part in candidate_name.strip().split():
            if len(part) > 2:
                redacted = re.sub(re.escape(part), "[REDACTED_NAME]", redacted, flags=re.IGNORECASE)

    # 4. Redact gender cues and pronouns
    for pattern, replacement in PRONOUN_MAP.items():
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)

    # Redact age & graduation year proxies
    for pat in AGE_PATTERNS:
        redacted = re.sub(pat, "[REDACTED_DATE]", redacted, flags=re.IGNORECASE)

    # Redact institution names if configured
    if redact_institutions and institutions:
        for inst in institutions:
            if len(inst.strip()) > 3:
                redacted = re.sub(re.escape(inst.strip()), "[REDACTED_INSTITUTION]", redacted, flags=re.IGNORECASE)

    return redacted


def redact_parsed_data(
    parsed_data: dict[str, Any],
    redact_institutions: bool = False,
) -> dict[str, Any]:
    """Return a sanitized copy of parsed resume data with protected attributes stripped."""
    data = dict(parsed_data)

    data["name"] = "[REDACTED_NAME]"
    data["email"] = "[REDACTED_EMAIL]"
    data["phone"] = "[REDACTED_PHONE]"
    data["location"] = "[REDACTED_LOCATION]"

    # Sanitize education entries (strip graduation year and optionally institution)
    clean_edu = []
    for edu in data.get("education", []):
        edu_copy = dict(edu)
        edu_copy["year"] = None
        if redact_institutions:
            edu_copy["institution"] = "[REDACTED_INSTITUTION]"
        clean_edu.append(edu_copy)
    data["education"] = clean_edu

    return data
