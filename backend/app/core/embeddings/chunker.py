"""Resume semantic chunker with character offsets for evidence highlighting."""

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass
class ResumeChunk:
    """A semantic chunk of a candidate resume with provenance metadata and offsets."""
    chunk_id: str
    chunk_type: str  # "experience" | "project" | "skill" | "education" | "summary"
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    start_char: int | None = None
    end_char: int | None = None

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "chunk_type": self.chunk_type,
            "text": self.text,
            "metadata": self.metadata,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }


def find_text_offsets(raw_text: str, snippet: str) -> tuple[int | None, int | None]:
    """Find start and end character offsets of snippet in raw resume text."""
    if not raw_text or not snippet:
        return None, None

    # Try exact match
    idx = raw_text.find(snippet)
    if idx != -1:
        return idx, idx + len(snippet)

    # Try case-insensitive search
    match = re.search(re.escape(snippet[:50]), raw_text, re.IGNORECASE)
    if match:
        start = match.start()
        end = min(len(raw_text), start + len(snippet))
        return start, end

    return None, None


def chunk_resume(parsed_data: dict, raw_text: str = "") -> list[ResumeChunk]:
    """Break structured resume data into semantic chunks for two-stage retrieval."""
    chunks: list[ResumeChunk] = []
    chunk_counter = 0

    # 1. Summary Chunk
    summary = parsed_data.get("summary")
    if summary and summary.strip():
        start, end = find_text_offsets(raw_text, summary)
        chunks.append(
            ResumeChunk(
                chunk_id=f"chk_{chunk_counter}",
                chunk_type="summary",
                text=summary.strip(),
                metadata={"section": "summary"},
                start_char=start,
                end_char=end,
            )
        )
        chunk_counter += 1

    # 2. Work Experience Chunks (one chunk per bullet or role description)
    for exp_idx, exp in enumerate(parsed_data.get("work_experience", [])):
        company = exp.get("company", "Unknown Company")
        title = exp.get("title", "Role")
        bullets = exp.get("bullets", [])
        start_date = exp.get("start_date")
        end_date = exp.get("end_date")

        role_header = f"{title} at {company}"

        if bullets:
            for b_idx, bullet in enumerate(bullets):
                bullet_clean = bullet.strip()
                if not bullet_clean:
                    continue
                full_chunk_text = f"{role_header}: {bullet_clean}"
                start, end = find_text_offsets(raw_text, bullet_clean)
                chunks.append(
                    ResumeChunk(
                        chunk_id=f"chk_{chunk_counter}",
                        chunk_type="experience",
                        text=full_chunk_text,
                        metadata={
                            "company": company,
                            "title": title,
                            "start_date": start_date,
                            "end_date": end_date,
                            "role_index": exp_idx,
                            "bullet_index": b_idx,
                        },
                        start_char=start,
                        end_char=end,
                    )
                )
                chunk_counter += 1
        else:
            # Whole role chunk if no bullets
            start, end = find_text_offsets(raw_text, company)
            chunks.append(
                ResumeChunk(
                    chunk_id=f"chk_{chunk_counter}",
                    chunk_type="experience",
                    text=role_header,
                    metadata={"company": company, "title": title, "start_date": start_date, "end_date": end_date},
                    start_char=start,
                    end_char=end,
                )
            )
            chunk_counter += 1

    # 3. Project Chunks
    for proj_idx, proj in enumerate(parsed_data.get("projects", [])):
        p_name = proj.get("name", f"Project {proj_idx+1}")
        p_desc = proj.get("description", "")
        p_tech = proj.get("technologies", [])
        tech_str = f" Technologies: {', '.join(p_tech)}." if p_tech else ""
        p_text = f"Project {p_name}: {p_desc}{tech_str}".strip()

        start, end = find_text_offsets(raw_text, p_desc or p_name)
        chunks.append(
            ResumeChunk(
                chunk_id=f"chk_{chunk_counter}",
                chunk_type="project",
                text=p_text,
                metadata={"name": p_name, "technologies": p_tech},
                start_char=start,
                end_char=end,
            )
        )
        chunk_counter += 1

    # 4. Skill Group Chunks
    skills = parsed_data.get("skills", [])
    if skills:
        skills_text = f"Technical Skills: {', '.join(skills)}"
        start, end = find_text_offsets(raw_text, skills[0] if skills else "")
        chunks.append(
            ResumeChunk(
                chunk_id=f"chk_{chunk_counter}",
                chunk_type="skill",
                text=skills_text,
                metadata={"skills_list": skills},
                start_char=start,
                end_char=end,
            )
        )
        chunk_counter += 1

    # 5. Education Chunks
    for edu in parsed_data.get("education", []):
        institution = edu.get("institution") or ""
        degree = edu.get("degree") or ""
        year = edu.get("year") or ""
        edu_text = f"Education: {degree} from {institution} ({year})".strip()

        start, end = find_text_offsets(raw_text, institution or degree)
        chunks.append(
            ResumeChunk(
                chunk_id=f"chk_{chunk_counter}",
                chunk_type="education",
                text=edu_text,
                metadata={"institution": institution, "degree": degree, "year": year},
                start_char=start,
                end_char=end,
            )
        )
        chunk_counter += 1

    return chunks
