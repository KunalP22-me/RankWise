"""Rule-based section heuristics and entity extraction from raw resume text."""

import re

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(
    r"(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b)"
)

# Common section headers
SECTION_PATTERNS = {
    "summary": re.compile(r"^(?:summary|professional summary|executive summary|profile|about me)\b", re.IGNORECASE),
    "experience": re.compile(r"^(?:work experience|experience|employment history|professional experience|work history)\b", re.IGNORECASE),
    "skills": re.compile(r"^(?:technical skills|skills|technologies|competencies|core competencies|tools)\b", re.IGNORECASE),
    "education": re.compile(r"^(?:education|academic background|academics|degrees)\b", re.IGNORECASE),
    "projects": re.compile(r"^(?:projects|personal projects|key projects|academic projects)\b", re.IGNORECASE),
    "certifications": re.compile(r"^(?:certifications|certificates|licenses)\b", re.IGNORECASE),
}

COMMON_SKILLS = {
    "python", "java", "c++", "c#", "go", "golang", "rust", "javascript", "typescript",
    "react", "angular", "vue", "next.js", "node.js", "fastapi", "flask", "django",
    "sql", "postgresql", "mysql", "mongodb", "redis", "cassandra", "kafka", "rabbitmq",
    "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd", "git", "linux", "terraform",
    "pytorch", "tensorflow", "scikit-learn", "keras", "pandas", "numpy", "faiss",
    "nlp", "llm", "rag", "rest api", "graphql", "microservices", "distributed systems"
}


def extract_contact_info(text: str) -> dict[str, str | None]:
    """Extract email, phone, location, and name from header."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    email_match = EMAIL_REGEX.search(text)
    email = email_match.group(0) if email_match else None

    phone_match = PHONE_REGEX.search(text)
    phone = phone_match.group(0) if phone_match else None

    # Name heuristic: inspect first 3 non-empty lines
    name = None
    for line in lines[:4]:
        # Skip if contains email, phone, URL, or section heading
        if EMAIL_REGEX.search(line) or PHONE_REGEX.search(line) or "http" in line or "@" in line:
            continue
        if len(line.split()) <= 4 and re.match(r"^[A-Z][A-Za-z\s.\-']+$", line):
            name = line
            break

    # Location heuristic: search for City, ST or City, Country pattern
    loc_match = re.search(r"\b([A-Z][a-zA-Z\s]+,\s*[A-Z]{2}\b|[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z]+)", text[:1000])
    location = loc_match.group(0).strip() if loc_match else None

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
    }


def split_into_sections(text: str) -> dict[str, str]:
    """Split resume text into named sections based on header line heuristics."""
    sections: dict[str, list[str]] = {"header": []}
    current_section = "header"

    for line in text.split("\n"):
        clean_line = line.strip()
        if not clean_line:
            continue

        matched_section = None
        # Check if line matches a known section header
        if len(clean_line) < 40:
            for sec_name, regex in SECTION_PATTERNS.items():
                if regex.match(clean_line.rstrip(":")):
                    matched_section = sec_name
                    break

        if matched_section:
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(clean_line)

    return {sec: "\n".join(lines).strip() for sec, lines in sections.items()}


def extract_skills_from_text(skills_text: str, full_text: str) -> list[str]:
    """Extract skills from skills section or fallback to scanning full text against skill dictionary."""
    found_skills = set()

    # Split by commas, bullets, pipes, or newlines in skills section
    if skills_text:
        parts = re.split(r"[,•|\n;]+", skills_text)
        for part in parts:
            item = part.strip().rstrip(".")
            if 1 < len(item) < 35:
                # Remove prefixes like "Languages:", "Frameworks:"
                if ":" in item:
                    item = item.split(":", 1)[1].strip()
                if item:
                    found_skills.add(item)

    # Also check presence of common skills across full text
    full_lower = full_text.lower()
    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, full_lower):
            # Normalize casing
            found_skills.add(skill.title() if len(skill) > 3 else skill.upper())

    return sorted(list(found_skills))


def parse_work_experience(exp_text: str) -> list[dict]:
    """Parse work experience block into structured role entries."""
    if not exp_text:
        return []

    entries: list[dict] = []
    current_entry: dict | None = None

    lines = exp_text.split("\n")
    date_pattern = re.compile(
        r"(?:(20\d{2}|19\d{2})[-/\.](0[1-9]|1[0-2])|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:20\d{2}|19\d{2})|(?:20\d{2}|19\d{2}))"
        r"\s*(?:-|–|—|to)\s*"
        r"(?:(Present|Current|Now)|(?:(20\d{2}|19\d{2})[-/\.](0[1-9]|1[0-2])|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:20\d{2}|19\d{2})|(?:20\d{2}|19\d{2})))",
        re.IGNORECASE,
    )

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        date_match = date_pattern.search(clean)
        # If line contains a date range and appears to be a job title/company header
        if date_match and len(clean) < 120 and (not clean.startswith(("•", "-", "*"))):
            if current_entry:
                entries.append(current_entry)

            # Extract date tokens
            start_str = date_match.group(1) or ""
            end_str = date_match.group(3) or date_match.group(4) or "Present"

            # Title / company is remainder of line
            title_part = clean[:date_match.start()].strip(" ,-–|")
            current_entry = {
                "company": title_part or "Unknown Company",
                "title": title_part,
                "start_date": start_str,
                "end_date": end_str,
                "bullets": [],
            }
        else:
            if current_entry:
                if clean.startswith(("•", "-", "*")):
                    current_entry["bullets"].append(clean.lstrip("•-* ").strip())
                elif len(current_entry["bullets"]) == 0 and not current_entry.get("company"):
                    current_entry["company"] = clean
                else:
                    current_entry["bullets"].append(clean)
            else:
                # Initial entry before date line
                current_entry = {
                    "company": clean,
                    "title": clean,
                    "start_date": None,
                    "end_date": None,
                    "bullets": [],
                }

    if current_entry:
        entries.append(current_entry)

    return entries


def parse_education(edu_text: str) -> list[dict]:
    """Parse education section into institution, degree, and year."""
    if not edu_text:
        return []

    entries: list[dict] = []
    lines = edu_text.split("\n")

    current: dict = {}
    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", clean)
        year = year_match.group(0) if year_match else None

        degree_match = re.search(
            r"\b(Bachelor(?:'s)?|B\.?S\.?|B\.?A\.?|Master(?:'s)?|M\.?S\.?|Ph\.?D\.?|Associate(?:'s)?)\b",
            clean,
            re.IGNORECASE,
        )

        if degree_match or "University" in clean or "College" in clean or "Institute" in clean:
            if current:
                entries.append(current)
            current = {
                "institution": clean if ("University" in clean or "College" in clean) else None,
                "degree": clean if degree_match else None,
                "field": None,
                "year": year,
            }
        elif current:
            if not current["institution"] and ("University" in clean or "College" in clean):
                current["institution"] = clean
            elif not current["degree"] and degree_match:
                current["degree"] = clean
            elif year and not current["year"]:
                current["year"] = year

    if current:
        entries.append(current)

    return entries
