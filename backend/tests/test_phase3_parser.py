"""Phase 3 tests — Resume parsing engine, PyMuPDF, python-docx, date math, heuristics, and LLM fallback."""

from pathlib import Path
import docx
import fitz  # PyMuPDF
import pytest

from app.core.parser import (
    ResumeParserPipeline,
    calculate_experience_years,
    compute_parse_confidence,
    extract_text_from_docx,
    extract_text_from_pdf,
    parse_date_point,
)
from app.core.parser.section_heuristics import (
    extract_contact_info,
    extract_skills_from_text,
    parse_education,
    parse_work_experience,
    split_into_sections,
)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a temporary valid PDF file with sample resume text."""
    pdf_path = tmp_path / "resume_sample.pdf"
    doc = fitz.open()
    page = doc.new_page()

    resume_text = (
        "Sarah Jenkins\n"
        "sarah.jenkins@example.com | (555) 234-5678 | Seattle, WA\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Lead DevOps engineer with 7 years experience designing cloud infrastructure.\n\n"
        "SKILLS\n"
        "Python, Docker, Kubernetes, AWS, Terraform, CI/CD, PostgreSQL\n\n"
        "EXPERIENCE\n"
        "CloudScale Systems | Lead Infrastructure Engineer\n"
        "2021-01 - Present\n"
        "• Architected multi-region Kubernetes clusters on AWS.\n"
        "• Reduced cloud infrastructure spend by 30% via autoscaling.\n\n"
        "DataWave Inc | DevOps Engineer\n"
        "2018-06 - 2020-12\n"
        "• Implemented automated CI/CD deployment pipelines using GitHub Actions.\n\n"
        "EDUCATION\n"
        "University of Washington\n"
        "Bachelor of Science in Computer Science, 2018\n"
    )

    page.insert_text((50, 50), resume_text, fontsize=10)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_docx(tmp_path: Path) -> Path:
    """Create a temporary valid DOCX file with sample resume text."""
    docx_path = tmp_path / "resume_sample.docx"
    doc = docx.Document()
    doc.add_heading("Marcus Vance", 0)
    doc.add_paragraph("marcus.vance@example.com | 555-876-5432 | Austin, TX")
    doc.add_heading("Skills", level=1)
    doc.add_paragraph("Python, Django, FastAPI, PostgreSQL, Redis, Docker")
    doc.add_heading("Experience", level=1)
    doc.add_paragraph("FinTech Solutions — Senior Backend Engineer (2020-03 to Present)")
    doc.add_paragraph("• Built payment gateway processing $5M daily transactions.")
    doc.add_heading("Education", level=1)
    doc.add_paragraph("University of Texas — B.S. in Software Engineering, 2019")
    doc.save(str(docx_path))
    return docx_path


class TestDocumentExtractors:
    """Test PyMuPDF and python-docx text extractors."""

    def test_extract_pdf_content(self, sample_pdf: Path):
        text, warnings = extract_text_from_pdf(sample_pdf)
        assert "Sarah Jenkins" in text
        assert "sarah.jenkins@example.com" in text
        assert "Kubernetes" in text
        assert len(warnings) == 0

    def test_extract_docx_content(self, sample_docx: Path):
        text, warnings = extract_text_from_docx(sample_docx)
        assert "Marcus Vance" in text
        assert "marcus.vance@example.com" in text
        assert "PostgreSQL" in text
        assert len(warnings) == 0

    def test_scanned_unreadable_pdf_warning(self, tmp_path: Path):
        """A PDF with negligible text must return an explicit warning instead of crashing."""
        blank_pdf = tmp_path / "blank.pdf"
        doc = fitz.open()
        doc.new_page()  # empty page
        doc.save(str(blank_pdf))
        doc.close()

        text, warnings = extract_text_from_pdf(blank_pdf)
        assert len(text) < 50
        assert any("unreadable_pdf_detected" in w for w in warnings)


class TestDateCalculation:
    """Test date parsing and overlap-aware years of experience calculations."""

    def test_parse_date_point(self):
        dt_present = parse_date_point("Present")
        assert dt_present is not None
        assert dt_present.year >= 2024

        dt_year = parse_date_point("2021")
        assert dt_year.year == 2021

        dt_month_year = parse_date_point("2021-05")
        assert dt_month_year.year == 2021
        assert dt_month_year.month == 5

    def test_consecutive_roles_experience(self):
        exps = [
            {"start_date": "2018-01-01", "end_date": "2020-01-01"},  # 2 years
            {"start_date": "2020-01-01", "end_date": "2022-01-01"},  # 2 years
        ]
        years = calculate_experience_years(exps)
        assert 3.9 <= years <= 4.1

    def test_overlapping_roles_experience(self):
        """Overlapping jobs should not be double-counted."""
        exps = [
            {"start_date": "2020-01-01", "end_date": "2022-01-01"},  # 2 years: 2020-2022
            {"start_date": "2021-01-01", "end_date": "2023-01-01"},  # 2 years: 2021-2023
        ]
        # Merged span: 2020-01 to 2023-01 = 3.0 years (not 4.0!)
        years = calculate_experience_years(exps)
        assert 2.9 <= years <= 3.1

    def test_experience_gaps(self):
        exps = [
            {"start_date": "2018-01-01", "end_date": "2019-01-01"},  # 1 year
            # 1 year gap
            {"start_date": "2020-01-01", "end_date": "2021-01-01"},  # 1 year
        ]
        years = calculate_experience_years(exps)
        assert 1.9 <= years <= 2.1


class TestSectionHeuristics:
    """Test contact, section, skill, and entity heuristics."""

    def test_contact_extraction(self):
        text = "David Miller\nEmail: david.miller@tech.org\nPhone: (415) 555-0144\nSan Francisco, CA"
        contact = extract_contact_info(text)
        assert contact["name"] == "David Miller"
        assert contact["email"] == "david.miller@tech.org"
        assert "555" in (contact["phone"] or "")

    def test_skills_extraction(self):
        skills_text = "Python, PyTorch, Docker, Kafka, AWS"
        full_text = "Built services with Python and deployed on AWS."
        skills = extract_skills_from_text(skills_text, full_text)
        assert "Python" in skills
        assert "Docker" in skills or "DOCKER" in skills


class TestParserPipeline:
    """Test end-to-end hybrid parser pipeline and confidence scoring."""

    def test_clean_resume_rules_parsing(self, sample_pdf: Path):
        pipeline = ResumeParserPipeline()
        result = pipeline.parse_file(sample_pdf)

        assert result["raw_text"] != ""
        assert result["parse_confidence"] >= 0.60
        assert result["parse_method"] == "rules"
        assert result["total_experience_years"] > 0
        assert "Sarah Jenkins" in result["parsed_data"]["name"]

    def test_low_confidence_triggers_llm_fallback(self, tmp_path: Path):
        """Unconventional or poorly structured resume triggers LLM fallback parser."""
        odd_pdf = tmp_path / "odd_resume.pdf"
        doc = fitz.open()
        page = doc.new_page()
        # Text with no clear section headers
        odd_text = (
            "Alex Mercer lives in Seattle. Code ninja who loves building big distributed things. "
            "Worked at Nexus Tech as a Senior Engineer from 2021 to now. Python Kafka Docker."
        )
        page.insert_text((50, 50), odd_text)
        doc.save(str(odd_pdf))
        doc.close()

        pipeline = ResumeParserPipeline()
        result = pipeline.parse_file(odd_pdf)

        assert result["parse_method"] == "llm_fallback"
        assert result["parse_confidence"] >= 0.80
        assert result["parsed_data"]["name"] is not None
