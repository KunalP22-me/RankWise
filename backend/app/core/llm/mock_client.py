"""Deterministic Mock LLM Client for offline testing and local execution."""

import json
from typing import TypeVar
from pydantic import BaseModel

from app.core.llm.base import LLMClient
from app.schemas.candidate import ResumeData
from app.schemas.job import BiasFlag, JDBiasCheckResult, JobRequirements, Requirement
from app.schemas.llm import (
    LLMCandidateExplanation,
    LLMChatResponse,
    LLMEvidenceVerdict,
    LLMResumeExtraction,
)

T = TypeVar("T", bound=BaseModel)


class MockLLMClient(LLMClient):
    """Mock LLM Client producing deterministic, schema-compliant outputs without API keys."""

    def __init__(self, model_name: str = "mock-v1"):
        super().__init__(model_name=model_name)

    def generate_text(self, prompt: str, temperature: float = 0.0) -> str:
        """Produce deterministic mock responses based on prompt keywords."""
        prompt_lower = prompt.lower()

        # Candidate Explanation
        if "<candidate_evidence>" in prompt or "<job_title>" in prompt or ("interview_questions" in prompt_lower and "strengths" in prompt_lower):
            return json.dumps({
                "strengths": [
                    "Strong demonstrated production experience with Python and high-throughput Kafka streaming pipelines.",
                    "Proven track record of distributed systems optimization at scale (10M events/day)."
                ],
                "gaps": [
                    "Limited explicit evidence of Kubernetes orchestration in production.",
                    "No listed experience leading cross-functional architectural committees."
                ],
                "interview_questions": [
                    "How did you handle consumer group rebalancing and message deduplication in your Kafka pipeline?",
                    "Can you walk through your PyTorch inference batching approach and how you measured latency tradeoffs?",
                    "Describe how you design disaster recovery and fallback mechanisms when downstream databases experience degradation."
                ],
                "summary": "Alex is a strong candidate whose technical background closely aligns with the Senior Backend role. Their 6 years of hands-on experience and demonstrated success optimizing high-scale streaming architectures make them well-suited for the team's immediate pipeline challenges."
            })

        # Evidence judging
        elif "<candidate_evidence_snippets>" in prompt or "<requirement>" in prompt or "verdict" in prompt_lower:
            snippets_body = prompt_lower
            if "<candidate_evidence_snippets>" in prompt:
                snippets_body = prompt.split("<candidate_evidence_snippets>")[1].split("</candidate_evidence_snippets>")[0].lower()

            # Check for false positive or hobby specifically inside candidate snippets
            if "gaming club" in snippets_body or "hobby" in snippets_body:
                return json.dumps({
                    "verdict": "None",
                    "reason": "Mention is strictly in a personal hobby/recreational context with no production experience."
                })
            elif "strong" in snippets_body or "kafka" in snippets_body or "python" in snippets_body:
                return json.dumps({
                    "verdict": "Strong",
                    "reason": "Candidate has hands-on production experience directly fulfilling the requirement."
                })
            else:
                return json.dumps({
                    "verdict": "Partial",
                    "reason": "Candidate demonstrates related conceptual knowledge or adjacent tool usage."
                })

        # Resume Extraction
        elif "<resume_content>" in prompt or "resume information" in prompt_lower:
            return json.dumps({
                "name": "Alex Mercer",
                "email": "alex.mercer@example.com",
                "phone": "+1-555-0199",
                "location": "San Francisco, CA",
                "summary": "Senior Software Engineer with 6 years building distributed systems and machine learning services.",
                "skills": ["Python", "FastAPI", "PyTorch", "Docker", "PostgreSQL", "Kafka"],
                "work_experience": [
                    {
                        "company": "Nexus Technologies",
                        "title": "Senior Backend Engineer",
                        "start_date": "2021-03",
                        "end_date": "Present",
                        "bullets": [
                            "Architected real-time streaming pipeline processing 10M events/day using Kafka and FastAPI.",
                            "Optimized PyTorch model inference throughput by 42% through batching and quantization."
                        ],
                        "duration_months": 36
                    },
                    {
                        "company": "DataSphere Labs",
                        "title": "Software Engineer",
                        "start_date": "2018-06",
                        "end_date": "2021-02",
                        "bullets": [
                            "Built high-availability REST APIs using Python and PostgreSQL.",
                            "Implemented automated CI/CD deployment pipelines on AWS."
                        ],
                        "duration_months": 32
                    }
                ],
                "projects": [
                    {
                        "name": "Mini-Vector Search",
                        "description": "Embedded retrieval engine built with FAISS and sentence embeddings.",
                        "technologies": ["Python", "FAISS", "Sentence-Transformers"]
                    }
                ],
                "education": [
                    {
                        "institution": "University of Washington",
                        "degree": "Bachelor of Science",
                        "field": "Computer Science",
                        "year": "2018"
                    }
                ],
                "certifications": ["AWS Certified Solutions Architect"]
            })

        # JD Extraction
        elif "<job_description>" in prompt and ("must_have" in prompt_lower or "implied" in prompt_lower):
            return json.dumps({
                "must_have": [
                    {
                        "text": "5+ years software engineering experience in Python",
                        "type": "must_have",
                        "category": "experience",
                        "implied_skills": ["Python", "Software Architecture"]
                    },
                    {
                        "text": "Production experience building data pipelines with Apache Kafka or similar message queues",
                        "type": "must_have",
                        "category": "skill",
                        "implied_skills": ["Kafka", "Distributed Systems", "ETL"]
                    }
                ],
                "nice_to_have": [
                    {
                        "text": "Experience with PyTorch or modern deep learning frameworks",
                        "type": "nice_to_have",
                        "category": "skill",
                        "implied_skills": ["PyTorch", "Machine Learning"]
                    }
                ],
                "minimum_experience_years": 5,
                "seniority_level": "Senior",
                "education_requirement": "Bachelor's degree in Computer Science or equivalent practical experience",
                "responsibilities": [
                    "Design and implement scalable distributed services",
                    "Lead architecture reviews and mentor junior developers"
                ],
                "implied_skills": ["Python", "Kafka", "Distributed Systems", "SQL", "ETL", "PyTorch"]
            })

        # JD Bias Check
        elif "exclusionary" in prompt_lower or "bias" in prompt_lower:
            flags = []
            jd_body = prompt_lower
            if "<job_description>" in prompt:
                jd_body = prompt.split("<job_description>")[1].split("</job_description>")[0].lower()

            if "young" in jd_body or "recent graduate" in jd_body:
                flags.append({
                    "original_text": "young and energetic",
                    "issue": "Age-discriminatory phrasing that may deter experienced applicants.",
                    "suggestion": "driven and motivated professional",
                    "severity": "high"
                })
            if "rockstar" in jd_body:
                flags.append({
                    "original_text": "rockstar",
                    "issue": "Masculine-coded jargon that decreases female applicant engagement.",
                    "suggestion": "high-performing software engineer",
                    "severity": "medium"
                })

            return json.dumps({
                "flags": flags,
                "overall_assessment": "Detected potentially biased wording issues." if flags else "No bias detected. Clear and inclusive posting.",
                "is_clean": len(flags) == 0
            })

        # Candidate Explanation
        elif "interview_questions" in prompt_lower or "strengths" in prompt_lower:
            return json.dumps({
                "strengths": [
                    "Strong demonstrated production experience with Python and high-throughput Kafka streaming pipelines.",
                    "Proven track record of distributed systems optimization at scale (10M events/day)."
                ],
                "gaps": [
                    "Limited explicit evidence of Kubernetes orchestration in production.",
                    "No listed experience leading cross-functional architectural committees."
                ],
                "interview_questions": [
                    "How did you handle consumer group rebalancing and message deduplication in your Kafka pipeline?",
                    "Can you walk through your PyTorch inference batching approach and how you measured latency tradeoffs?",
                    "Describe how you design disaster recovery and fallback mechanisms when downstream databases experience degradation."
                ],
                "summary": "Alex is a strong candidate whose technical background closely aligns with the Senior Backend role. Their 6 years of hands-on experience and demonstrated success optimizing high-scale streaming architectures make them well-suited for the team's immediate pipeline challenges."
            })

        # Recruiter Chat
        elif "recruiter assistant" in prompt_lower or "cited_snippets" in prompt_lower:
            return json.dumps({
                "answer": "Candidate Alex Mercer has extensive production Kafka experience, having architected real-time streaming pipelines processing over 10M events per day at Nexus Technologies.",
                "cited_snippets": [
                    {
                        "candidate_id": "cand-001",
                        "candidate_name": "Alex Mercer",
                        "snippet": "Architected real-time streaming pipeline processing 10M events/day using Kafka and FastAPI.",
                        "relevance": "Direct proof of production Kafka architecture"
                    }
                ],
                "confidence": "high"
            })

        # Counterfactual perturbation
        elif "counterfactual" in prompt_lower or "perturbed_text" in prompt_lower:
            return json.dumps({
                "perturbed_text": prompt.replace("Alex Mercer", "Priya Sharma").replace("he", "she").replace("his", "her"),
                "changes_made": ["Swapped name to Priya Sharma", "Swapped pronouns to she/her"]
            })

        # Default fallback
        return json.dumps({"status": "ok", "message": "Mock LLM output generated."})
