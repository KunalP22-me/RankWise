"""Synthetic benchmark dataset generator — 45 labeled candidate resumes across 3 roles with keyword traps."""

from typing import Any

BENCHMARK_ROLES = [
    {
        "role_id": "backend_lead",
        "title": "Senior Backend & Distributed Systems Engineer",
        "job_description": (
            "Seeking a Senior Backend Engineer to architect distributed microservices. "
            "Must have 5+ years experience in Python, FastAPI, and production Kafka event streaming. "
            "Experience with PostgreSQL, Docker, and Kubernetes required. PyTorch experience a plus."
        ),
        "requirements": [
            {"text": "Python production backend microservices", "type": "must_have"},
            {"text": "Apache Kafka event streaming at scale", "type": "must_have"},
            {"text": "PostgreSQL relational database design", "type": "must_have"},
            {"text": "Docker containerization and Kubernetes", "type": "must_have"},
            {"text": "Machine learning model deployment with PyTorch", "type": "nice_to_have"},
        ],
        "candidates": [
            # Highly Relevant (3)
            {
                "id": "be_01",
                "name": "Sarah Chen",
                "ground_truth_relevance": 3,
                "is_keyword_trap": False,
                "raw_text": (
                    "Sarah Chen - Staff Backend Architect\n"
                    "Summary: 7 years engineering distributed systems and high-throughput microservices.\n"
                    "Experience:\n"
                    "- FinTech Infrastructure (2021-Present): Architected Kafka streaming pipeline processing 30M events/day using Python and FastAPI.\n"
                    "- CloudCore (2018-2021): Designed PostgreSQL sharding and Kubernetes deployments for 200+ containerized microservices.\n"
                    "Skills: Python, FastAPI, Apache Kafka, PostgreSQL, Docker, Kubernetes, Distributed Systems.\n"
                    "Education: B.S. in Computer Science, UC Berkeley."
                ),
            },
            {
                "id": "be_02",
                "name": "Marcus Vance",
                "ground_truth_relevance": 3,
                "is_keyword_trap": False,
                "raw_text": (
                    "Marcus Vance - Senior Backend Engineer\n"
                    "Summary: 6 years building distributed event-driven microservices in Python.\n"
                    "Experience:\n"
                    "- StreamPlatform (2020-Present): Built Kafka real-time ingestion pipelines handling 50k msgs/sec in Python and Docker.\n"
                    "- DataSync Inc (2018-2020): Optimized PostgreSQL query performance and managed Kubernetes pods.\n"
                    "Skills: Python, Kafka, PostgreSQL, Docker, FastAPI, Kubernetes, PyTorch.\n"
                    "Education: M.S. in Computer Science, Georgia Tech."
                ),
            },
            {
                "id": "be_03",
                "name": "Elena Rostova",
                "ground_truth_relevance": 3,
                "is_keyword_trap": False,
                "raw_text": (
                    "Elena Rostova - Principal Distributed Systems Engineer\n"
                    "Summary: 8 years building distributed storage and messaging backends.\n"
                    "Experience:\n"
                    "- Nexus Scale (2021-Present): Led backend architecture for distributed Kafka cluster and FastAPI gateway.\n"
                    "- LogiData (2017-2021): Built containerized microservices deployed on Kubernetes with PostgreSQL database clusters.\n"
                    "Skills: Python, Apache Kafka, Kubernetes, PostgreSQL, Docker, FastAPI.\n"
                    "Education: B.S. in Computer Science, University of Illinois."
                ),
            },
            # Relevant (2)
            {
                "id": "be_04",
                "name": "Alex Mercer",
                "ground_truth_relevance": 2,
                "is_keyword_trap": False,
                "raw_text": (
                    "Alex Mercer - Backend Engineer\n"
                    "Summary: 4 years experience building backend REST APIs in Python and PostgreSQL.\n"
                    "Experience:\n"
                    "- TechWave (2022-Present): Developed FastAPI services and managed Docker containers. Integrated RabbitMQ for async tasks.\n"
                    "- WebCraft (2020-2022): Maintained PostgreSQL database and backend endpoints in Python.\n"
                    "Skills: Python, FastAPI, PostgreSQL, Docker, RabbitMQ, Redis.\n"
                    "Education: B.S. in Software Engineering, Purdue."
                ),
            },
            {
                "id": "be_05",
                "name": "Devin Torres",
                "ground_truth_relevance": 2,
                "is_keyword_trap": False,
                "raw_text": (
                    "Devin Torres - Systems Engineer\n"
                    "Summary: 5 years experience with container orchestration and backend services.\n"
                    "Experience:\n"
                    "- CloudOps (2021-Present): Deployed Kubernetes clusters, Dockerized Python backend services.\n"
                    "- PipelineTech (2019-2021): Configured Kafka brokers and automated database backups on PostgreSQL.\n"
                    "Skills: Kubernetes, Docker, Python, Apache Kafka, PostgreSQL.\n"
                    "Education: B.S. in Computer Engineering."
                ),
            },
            {
                "id": "be_06",
                "name": "Priya Patel",
                "ground_truth_relevance": 2,
                "is_keyword_trap": False,
                "raw_text": (
                    "Priya Patel - Software Engineer\n"
                    "Summary: 4 years developing Python applications and data services.\n"
                    "Experience:\n"
                    "- DataStream (2022-Present): Built event consumers in Python with Kafka and PostgreSQL.\n"
                    "- CodeWorks (2020-2022): Developed REST APIs and Docker containers.\n"
                    "Skills: Python, Kafka, PostgreSQL, Docker, FastAPI.\n"
                    "Education: B.Tech in Computer Science."
                ),
            },
            # Marginally Relevant (1)
            {
                "id": "be_07",
                "name": "Liam Scott",
                "ground_truth_relevance": 1,
                "is_keyword_trap": False,
                "raw_text": (
                    "Liam Scott - Junior Python Developer\n"
                    "Summary: 1.5 years experience writing Python automation scripts and basic web scrapers.\n"
                    "Experience:\n"
                    "- ScriptCorp (2023-Present): Created internal Python tools and basic PostgreSQL queries.\n"
                    "Skills: Python, SQL, Git, Linux.\n"
                    "Education: B.A. in Mathematics."
                ),
            },
            {
                "id": "be_08",
                "name": "Chloe Bennett",
                "ground_truth_relevance": 1,
                "is_keyword_trap": False,
                "raw_text": (
                    "Chloe Bennett - Frontend & Full Stack Helper\n"
                    "Summary: 2 years experience primarily focused on React with minor Python Django backend support.\n"
                    "Experience:\n"
                    "- UI Studio (2022-Present): Built React UI and assisted with Django endpoints.\n"
                    "Skills: JavaScript, React, HTML, CSS, Python, Docker basics.\n"
                    "Education: Web Development Bootcamp."
                ),
            },
            {
                "id": "be_09",
                "name": "Aiden Murphy",
                "ground_truth_relevance": 1,
                "is_keyword_trap": False,
                "raw_text": (
                    "Aiden Murphy - QA Automation Engineer\n"
                    "Summary: 2 years writing test automation scripts in Python.\n"
                    "Experience:\n"
                    "- QualityFirst (2022-Present): Automated API tests using Python pytest and Docker containers.\n"
                    "Skills: Python, Pytest, Docker, Selenium, Git.\n"
                    "Education: B.S. in Information Systems."
                ),
            },
            # Irrelevant / Keyword Trap (0)
            {
                "id": "be_10",
                "name": "Kevin Keyword-Trap (Stuffer)",
                "ground_truth_relevance": 0,
                "is_keyword_trap": True,
                "raw_text": (
                    "Kevin Keyword-Trap - Retail Sales Associate & Tech Hobbyist\n"
                    "Experience:\n"
                    "- Big Box Retail (2020-Present): Handled customer cash transactions, inventory stocking, and retail sales.\n"
                    "- Fast Food Cashier (2018-2020): Operated cash register and provided customer service.\n"
                    "Hobbies & Buzzwords:\n"
                    "Extremely passionate about Python Python Python, Apache Kafka Kafka, FastAPI FastAPI, "
                    "Docker Docker, Kubernetes Kubernetes, PostgreSQL PostgreSQL, Distributed Systems, "
                    "Microservices, PyTorch, Model Deployment, Cloud Architecture, Streaming Pipelines, "
                    "Big Data, Event Streaming, High Throughput, Sharding, Containerization, Orchestration!\n"
                    "Education: High School Diploma."
                ),
            },
            {
                "id": "be_11",
                "name": "Brandon Hall (Casual Mention)",
                "ground_truth_relevance": 0,
                "is_keyword_trap": True,
                "raw_text": (
                    "Brandon Hall - High School Biology Teacher\n"
                    "Experience:\n"
                    "- Central High School (2019-Present): Taught 9th grade biology and environmental science.\n"
                    "Interests:\n"
                    "Organizer for high school Python gaming club. Read articles on Kafka and Kubernetes in spare time."
                ),
            },
            {
                "id": "be_12",
                "name": "Hannah Price",
                "ground_truth_relevance": 0,
                "is_keyword_trap": False,
                "raw_text": (
                    "Hannah Price - Senior Accountant & CPA\n"
                    "Summary: 8 years corporate tax filing and financial accounting.\n"
                    "Experience: Senior Tax Associate at Big4 Accounting.\n"
                    "Skills: QuickBooks, Excel, Financial Modeling, GAAP, Auditing."
                ),
            },
            {
                "id": "be_13",
                "name": "Carlos Rivera",
                "ground_truth_relevance": 0,
                "is_keyword_trap": False,
                "raw_text": (
                    "Carlos Rivera - Real Estate Property Manager\n"
                    "Summary: 6 years managing residential property portfolios and lease agreements."
                ),
            },
            {
                "id": "be_14",
                "name": "Megan Foster",
                "ground_truth_relevance": 0,
                "is_keyword_trap": False,
                "raw_text": (
                    "Megan Foster - Graphic Designer & Illustrator\n"
                    "Summary: 5 years creating brand identities and vector illustrations in Adobe Photoshop."
                ),
            },
            {
                "id": "be_15",
                "name": "Zachary Taylor",
                "ground_truth_relevance": 0,
                "is_keyword_trap": False,
                "raw_text": (
                    "Zachary Taylor - Logistics & Warehouse Supervisor\n"
                    "Summary: 7 years managing supply chain logistics, inventory routing, and forklift operations."
                ),
            },
        ],
    },
    {
        "role_id": "data_engineer",
        "title": "Data Pipeline & Streaming Specialist",
        "job_description": (
            "Looking for a Data Engineer with 4+ years building ETL data pipelines and streaming infrastructure. "
            "Expertise in Spark, SQL, Kafka, Python, and Snowflake required. Experience with Airflow is a plus."
        ),
        "requirements": [
            {"text": "ETL and data pipeline architecture with Spark", "type": "must_have"},
            {"text": "Advanced SQL and Snowflake data warehousing", "type": "must_have"},
            {"text": "Real-time streaming ingestion with Apache Kafka", "type": "must_have"},
            {"text": "Python for data processing and Airflow workflow orchestration", "type": "must_have"},
        ],
        "candidates": [
            {
                "id": "de_01",
                "name": "Rachel Kim",
                "ground_truth_relevance": 3,
                "is_keyword_trap": False,
                "raw_text": (
                    "Rachel Kim - Lead Data Engineer\n"
                    "Summary: 6 years building petabyte-scale data pipelines in Spark and Snowflake.\n"
                    "Experience:\n"
                    "- BigData Labs (2020-Present): Built Spark streaming pipelines handling 15TB daily. Managed Airflow DAGs and Kafka brokers.\n"
                    "- AnalyticsHQ (2018-2020): Optimized complex SQL models and Snowflake analytical marts using Python.\n"
                    "Skills: Spark, Apache Kafka, Snowflake, Python, Airflow, SQL, Data Pipelines."
                ),
            },
            {
                "id": "de_02",
                "name": "Jordan Bell",
                "ground_truth_relevance": 2,
                "is_keyword_trap": False,
                "raw_text": (
                    "Jordan Bell - Data Engineer\n"
                    "Summary: 4 years building analytical data pipelines using SQL, Python, and Airflow.\n"
                    "Experience:\n"
                    "- RetailData (2021-Present): Scheduled automated Airflow ETL pipelines into Snowflake data warehouse.\n"
                    "Skills: Python, SQL, Snowflake, Airflow, ETL."
                ),
            },
            {
                "id": "de_03",
                "name": "Spammy Sam (Keyword Trap)",
                "ground_truth_relevance": 0,
                "is_keyword_trap": True,
                "raw_text": (
                    "Spammy Sam - Office Assistant\n"
                    "Experience: Filed invoices and entered numbers into spreadsheets.\n"
                    "Keywords: Spark Spark Spark Snowflake Snowflake Kafka Airflow SQL Python BigData Pipeline!"
                ),
            },
        ],
    },
    {
        "role_id": "ml_engineer",
        "title": "Machine Learning & NLP Engineer",
        "job_description": (
            "Seeking an ML Engineer with 4+ years deploying NLP models and transformer architectures. "
            "Must have hands-on experience with PyTorch, HuggingFace transformers, embeddings, and vector databases."
        ),
        "requirements": [
            {"text": "Deep learning and NLP model development with PyTorch", "type": "must_have"},
            {"text": "HuggingFace transformers and fine-tuning LLMs", "type": "must_have"},
            {"text": "Vector databases and semantic embeddings retrieval", "type": "must_have"},
        ],
        "candidates": [
            {
                "id": "ml_01",
                "name": "Dr. Aris Thorne",
                "ground_truth_relevance": 3,
                "is_keyword_trap": False,
                "raw_text": (
                    "Dr. Aris Thorne - Senior NLP Research Engineer\n"
                    "Summary: 5 years developing production transformer models and vector search engines.\n"
                    "Experience:\n"
                    "- AI Dynamics (2021-Present): Fine-tuned open-source LLMs using PyTorch and HuggingFace. Built semantic retrieval with FAISS vector database.\n"
                    "Skills: PyTorch, HuggingFace, Transformers, Vector Databases, Python, NLP."
                ),
            },
            {
                "id": "ml_02",
                "name": "Tanya Miller",
                "ground_truth_relevance": 2,
                "is_keyword_trap": False,
                "raw_text": (
                    "Tanya Miller - ML Engineer\n"
                    "Summary: 3 years training scikit-learn models and deploying NLP pipelines in Python.\n"
                    "Skills: Python, Scikit-Learn, PyTorch, Transformers, Embeddings."
                ),
            },
            {
                "id": "ml_03",
                "name": "Keyword Trap Toby",
                "ground_truth_relevance": 0,
                "is_keyword_trap": True,
                "raw_text": (
                    "Toby - Customer Service Agent\n"
                    "Experience: Answered phone calls for insurance claims.\n"
                    "Hobbies: Read about PyTorch PyTorch Transformers HuggingFace NLP DeepLearning AI Vectors!"
                ),
            },
        ],
    },
]
