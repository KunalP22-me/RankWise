"""Job Description Understanding package — requirements extraction, ontology, bias checking."""

from app.core.jd.bias_checker import check_jd_bias
from app.core.jd.extractor import extract_job_requirements
from app.core.jd.ontology import SkillOntology, ontology

__all__ = [
    "extract_job_requirements",
    "check_jd_bias",
    "SkillOntology",
    "ontology",
]
