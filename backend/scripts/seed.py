"""RankWise Database Seeder — populates demo jobs, candidates, rankings, and bias reports."""

import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import UTC, datetime
from app.database import Base, SessionLocal, create_tables, engine
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.override import Override
from app.models.ranking import CandidateRanking, RankingRun
from app.services.bias_service import BiasService
from app.services.ranking_service import RankingService


def seed_database():
    """Populate database with rich demo data for instant dashboard demonstration."""
    print("Initializing database tables...")
    create_tables()

    db = SessionLocal()
    try:
        # Check if already seeded
        existing_job = db.query(Job).first()
        if existing_job:
            print(f"Database already contains jobs (found: '{existing_job.title}'). Resetting demo data...")
            db.query(Override).delete()
            db.query(CandidateRanking).delete()
            db.query(RankingRun).delete()
            db.query(Candidate).delete()
            db.query(Job).delete()
            db.commit()

        print("Seeding demo jobs...")
        # 1. Senior Backend Engineer Job
        job_backend = Job(
            title="Senior Backend & Distributed Systems Engineer",
            description=(
                "We are looking for a Senior Backend Engineer to design and scale our distributed infrastructure. "
                "You will lead microservice development in Python, manage high-throughput Kafka event streaming pipelines, "
                "and deploy resilient services on Kubernetes with PostgreSQL database clusters."
            ),
            status="active",
            requirements_json={
                "must_have": [
                    {"text": "Python production backend microservices architecture", "type": "must_have", "category": "skill"},
                    {"text": "High-throughput Apache Kafka event streaming and consumer groups", "type": "must_have", "category": "skill"},
                    {"text": "PostgreSQL database design, indexing, and query optimization", "type": "must_have", "category": "skill"},
                    {"text": "Docker containerization and Kubernetes orchestration", "type": "must_have", "category": "skill"},
                ],
                "nice_to_have": [
                    {"text": "Experience with PyTorch or modern deep learning model serving", "type": "nice_to_have", "category": "skill"},
                    {"text": "Redis caching and message broker implementations", "type": "nice_to_have", "category": "skill"},
                ],
                "minimum_experience_years": 4,
                "seniority_level": "Senior",
                "education_requirement": "Bachelor's degree in Computer Science or equivalent practical experience",
            },
            weights={
                "must_have": 0.40,
                "nice_to_have": 0.15,
                "experience": 0.25,
                "education": 0.20,
            },
            blind_mode=False,
        )

        # 2. Data & Streaming Engineer Job
        job_data = Job(
            title="Lead Data Pipeline & Streaming Engineer",
            description=(
                "Join our data platform team building petabyte-scale data pipelines. "
                "Requires 5+ years building ETL architectures in Spark, SQL, Snowflake, and Apache Kafka."
            ),
            status="active",
            requirements_json={
                "must_have": [
                    {"text": "Apache Spark distributed ETL data pipelines", "type": "must_have", "category": "skill"},
                    {"text": "Real-time streaming ingestion with Apache Kafka", "type": "must_have", "category": "skill"},
                    {"text": "Snowflake data warehousing and advanced SQL modeling", "type": "must_have", "category": "skill"},
                ],
                "nice_to_have": [
                    {"text": "Apache Airflow DAG scheduling and monitoring", "type": "nice_to_have", "category": "skill"},
                ],
                "minimum_experience_years": 5,
                "education_requirement": "Bachelor's degree",
            },
            weights={"must_have": 0.45, "nice_to_have": 0.15, "experience": 0.25, "education": 0.15},
            blind_mode=False,
        )

        db.add_all([job_backend, job_data])
        db.commit()
        db.refresh(job_backend)
        db.refresh(job_data)

        print("Seeding candidates for Senior Backend Engineer...")
        candidates_data = [
            {
                "name": "Sarah Chen",
                "filename": "sarah_chen_resume.pdf",
                "total_exp": 7.0,
                "skills": ["Python", "FastAPI", "Apache Kafka", "PostgreSQL", "Docker", "Kubernetes", "PyTorch"],
                "raw_text": (
                    "Sarah Chen\nSan Francisco, CA | sarah.chen@example.com\n"
                    "Staff Backend Architect with 7 years engineering distributed systems and high-throughput microservices.\n"
                    "Work Experience:\n"
                    "- FinTech Infrastructure (2021-Present): Principal Architect for Kafka streaming pipeline processing 30M events/day using Python and FastAPI.\n"
                    "- CloudCore Systems (2018-2021): Designed PostgreSQL sharding and Kubernetes deployments for 200+ containerized microservices.\n"
                    "Education: B.S. in Computer Science, UC Berkeley, 2017."
                ),
                "parsed": {
                    "name": "Sarah Chen",
                    "email": "sarah.chen@example.com",
                    "phone": "+1-555-0144",
                    "location": "San Francisco, CA",
                    "summary": "Staff Backend Architect with 7 years engineering distributed systems and high-throughput microservices.",
                    "skills": ["Python", "FastAPI", "Apache Kafka", "PostgreSQL", "Docker", "Kubernetes", "PyTorch"],
                    "work_experience": [
                        {
                            "company": "FinTech Infrastructure",
                            "title": "Principal Backend Architect",
                            "start_date": "2021-02",
                            "end_date": "Present",
                            "bullets": [
                                "Architected Kafka streaming pipeline processing 30M events/day using Python and FastAPI.",
                                "Reduced end-to-end event latency from 450ms to 42ms through partition tuning and parallel consumer groups.",
                            ],
                        },
                        {
                            "company": "CloudCore Systems",
                            "title": "Senior Software Engineer",
                            "start_date": "2018-06",
                            "end_date": "2021-01",
                            "bullets": [
                                "Designed PostgreSQL sharding and database migrations for high-traffic financial ledgers.",
                                "Automated Kubernetes container deployments using Helm and Docker.",
                            ],
                        },
                    ],
                    "education": [{"institution": "UC Berkeley", "degree": "Bachelor of Science in Computer Science", "year": "2017"}],
                },
            },
            {
                "name": "Marcus Vance",
                "filename": "marcus_vance_resume.pdf",
                "total_exp": 5.5,
                "skills": ["Python", "FastAPI", "Kafka", "PostgreSQL", "Docker", "Kubernetes"],
                "raw_text": (
                    "Marcus Vance\nAustin, TX | marcus.v@example.com\n"
                    "Senior Backend Engineer with 5+ years building event-driven microservices in Python.\n"
                    "Work Experience:\n"
                    "- StreamPlatform (2020-Present): Built Kafka real-time ingestion pipelines handling 50k msgs/sec in Python and Docker.\n"
                    "- DataSync Inc (2018-2020): Optimized PostgreSQL query performance and managed Kubernetes pods.\n"
                    "Education: M.S. in Computer Science, Georgia Tech, 2018."
                ),
                "parsed": {
                    "name": "Marcus Vance",
                    "email": "marcus.v@example.com",
                    "location": "Austin, TX",
                    "summary": "Senior Backend Engineer with 5+ years building event-driven microservices in Python.",
                    "skills": ["Python", "FastAPI", "Kafka", "PostgreSQL", "Docker", "Kubernetes"],
                    "work_experience": [
                        {
                            "company": "StreamPlatform",
                            "title": "Senior Backend Engineer",
                            "start_date": "2020-04",
                            "end_date": "Present",
                            "bullets": [
                                "Built Kafka real-time ingestion pipelines handling 50k msgs/sec in Python and Docker.",
                                "Implemented FastAPI REST endpoints with async database pools.",
                            ],
                        },
                        {
                            "company": "DataSync Inc",
                            "title": "Backend Developer",
                            "start_date": "2018-08",
                            "end_date": "2020-03",
                            "bullets": [
                                "Optimized PostgreSQL query performance and managed Kubernetes pods.",
                            ],
                        },
                    ],
                    "education": [{"institution": "Georgia Tech", "degree": "Master of Science in Computer Science", "year": "2018"}],
                },
            },
            {
                "name": "Devin Torres",
                "filename": "devin_torres_resume.docx",
                "total_exp": 4.0,
                "skills": ["Python", "Docker", "PostgreSQL", "Kubernetes", "Redis"],
                "raw_text": (
                    "Devin Torres\nSeattle, WA\n"
                    "Software Engineer with 4 years experience deploying containerized Python backend services and PostgreSQL databases.\n"
                    "Work Experience:\n"
                    "- CloudOps (2021-Present): Deployed Kubernetes clusters and Dockerized Python backend services.\n"
                    "- PipelineTech (2019-2021): Configured Redis caching and automated database backups on PostgreSQL.\n"
                    "Education: B.S. in Computer Engineering, University of Washington, 2019."
                ),
                "parsed": {
                    "name": "Devin Torres",
                    "email": "devin.t@example.com",
                    "location": "Seattle, WA",
                    "summary": "Software Engineer with 4 years experience deploying containerized Python backend services and PostgreSQL databases.",
                    "skills": ["Python", "Docker", "PostgreSQL", "Kubernetes", "Redis"],
                    "work_experience": [
                        {
                            "company": "CloudOps",
                            "title": "Software Engineer",
                            "start_date": "2021-05",
                            "end_date": "Present",
                            "bullets": [
                                "Deployed Kubernetes clusters and Dockerized Python backend services.",
                                "Designed REST APIs for cloud deployment monitoring.",
                            ],
                        },
                        {
                            "company": "PipelineTech",
                            "title": "Junior Backend Developer",
                            "start_date": "2019-07",
                            "end_date": "2021-04",
                            "bullets": [
                                "Configured Redis caching and automated database backups on PostgreSQL.",
                            ],
                        },
                    ],
                    "education": [{"institution": "University of Washington", "degree": "B.S. in Computer Engineering", "year": "2019"}],
                },
            },
            {
                "name": "Kevin Keyword-Trap",
                "filename": "kevin_trap_resume.pdf",
                "total_exp": 1.0,
                "skills": ["Retail Sales", "Cashier"],
                "raw_text": (
                    "Kevin Keyword-Trap\nChicago, IL\n"
                    "Retail Sales Associate & Tech Enthusiast.\n"
                    "Experience:\n"
                    "- MegaStore Retail (2022-2023): Handled customer cash transactions and store stocking.\n"
                    "Hobbies & Buzzwords:\n"
                    "Huge interest in Python, Apache Kafka, FastAPI, Docker, Kubernetes, PostgreSQL, Distributed Systems, "
                    "Microservices, High Throughput Pipelines, PyTorch Model Serving!\n"
                    "Education: High School Diploma, 2021."
                ),
                "parsed": {
                    "name": "Kevin Keyword-Trap",
                    "email": "kevin.trap@example.com",
                    "location": "Chicago, IL",
                    "summary": "Retail Sales Associate & Tech Enthusiast.",
                    "skills": ["Retail Sales", "Cashier"],
                    "work_experience": [
                        {
                            "company": "MegaStore Retail",
                            "title": "Retail Sales Associate",
                            "start_date": "2022-01",
                            "end_date": "2023-01",
                            "bullets": ["Handled customer cash transactions and store stocking."],
                        }
                    ],
                    "education": [{"institution": "Lincoln High School", "degree": "High School Diploma", "year": "2021"}],
                },
            },
        ]

        for cand in candidates_data:
            c = Candidate(
                job_id=job_backend.id,
                filename=cand["filename"],
                file_path=f"uploads/{cand['filename']}",
                file_type="pdf" if cand["filename"].endswith(".pdf") else "docx",
                raw_text=cand["raw_text"],
                parsed_data=cand["parsed"],
                parse_method="rules",
                parse_confidence=0.92 if "Trap" not in cand["name"] else 0.50,
                total_experience_years=cand["total_exp"],
                status="parsed",
            )
            db.add(c)
        db.commit()

        print("Executing full ranking pipeline for Senior Backend Engineer...")
        ranking_service = RankingService(db)
        run = ranking_service.execute_ranking(job_backend.id)
        print(f"Ranking run completed successfully: Run ID {run.id}")

        print("Generating Bias & Fairness report...")
        bias_service = BiasService(db)
        bias_report = bias_service.generate_bias_report(run.id)
        print(f"Bias report generated (Status: Flagged={bias_report.flagged})")

        # Add sample recruiter override to demonstrate human-in-the-loop feature
        if run.candidate_rankings:
            top_cand = run.candidate_rankings[0]
            top_cand.overridden_score = 0.96
            ov = Override(
                candidate_ranking_id=top_cand.id,
                criterion="overall",
                original_score=top_cand.overall_score,
                new_score=0.96,
                reason_category="domain_expertise",
                reason_text="Exceptional open-source Kafka contribution verified during pre-screen.",
                user="recruiter_lead",
                created_at=datetime.now(UTC),
            )
            db.add(ov)
            db.commit()
            print("Sample recruiter override created.")

        print("\n Seeding Complete! Ready to launch RankWise.")
        print("To start the backend:   uvicorn app.main:app --reload --port 8000")
        print("To start the dashboard: streamlit run streamlit_app.py")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
