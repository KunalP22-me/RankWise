# RankWise: AI Agent Project Handover & Developer Guide

> **NOTE FOR AI AGENTS (Antigravity / Coding Assistant):**  
> If you are continuing work on this codebase in a new session or after memory compaction, **READ THIS FILE FIRST**. It describes the entire architecture, directory map, design invariants, operational commands, and lessons learned.

---

## 1. Project Mission & Core Invariant

RankWise is an AI-powered resume screening, semantic matching, and explainable candidate ranking platform built with a Python **FastAPI** backend, SQLite (WAL mode) database, and a **Streamlit** recruiter dashboard.

### ⚠️ The Non-Negotiable Core Principle
> **"The LLM reads and explains; deterministic code scores."**

- **The LLM NEVER outputs the final numeric ranking score.**
- The LLM's role is restricted to:
  1. Extracting structured entities (skills, experience, education, dates).
  2. Categorical evidence judging: `Strong`, `Partial`, or `None` on a per-requirement basis, with a grounded 1-sentence reason.
  3. Generating natural language explanations (strengths, gaps, interview questions).
- **Deterministic Python code calculates all numbers** using auditable mathematical formulas:
  $$\text{ReqScore} = \text{VerdictMultiplier} \times (0.45 \cdot \text{Sim} + 0.30 \cdot \text{LocWeight} + 0.15 \cdot \text{Recency} + 0.10 \cdot \text{Duration})$$
  Clamped strictly to `0.0` if verdict is `None` (preventing keyword-stuffing exploits).
- Final score is a transparent weighted sum of Must-Have, Nice-to-Have, Experience Fit, and Education Fit scores.

---

## 2. Directory & Component Map

```
c:\Users\gamer\Desktop\minor proj\
├── AGENTS.md                          # <-- THIS HANDOVER FILE
├── PROJECT_STATE.md                   # Detailed component registry & phase status
├── README.md                          # User-facing README with benchmark tables & diagram
├── streamlit_app.py                   # Root wrapper for Streamlit runner
├── backend/
│   ├── rankwise.db                    # SQLite database (persisted demo data)
│   ├── streamlit_app.py               # Complete 8-view Streamlit Recruiter Dashboard
│   ├── requirements.txt               # Dependencies
│   ├── data/
│   │   └── skill_ontology.json        # 200+ skill taxonomy graph with aliases & relationships
│   ├── scripts/
│   │   └── seed.py                    # Complete demonstration data seeder
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint (prefix="/api", lifespan DB setup)
│   │   ├── config.py                  # Pydantic Settings (.env, LLM providers, paths)
│   │   ├── database.py                # SQLAlchemy engine (WAL mode, SQLite/Postgres)
│   │   ├── models/                    # SQLAlchemy 2.0 ORM models
│   │   │   ├── job.py                 # Job model (requirements_json, weights, blind_mode)
│   │   │   ├── candidate.py           # Candidate & CandidateResume models
│   │   │   ├── ranking.py             # RankingRun & CandidateRanking models
│   │   │   ├── override.py            # RecruiterOverride model (audit reason, user_id)
│   │   │   └── audit_log.py           # AuditLog model (immutable event logging, detail JSON)
│   │   ├── schemas/                   # Pydantic validation schemas
│   │   │   ├── job.py, candidate.py, ranking.py, override.py, chat.py
│   │   ├── repositories/              # Database data access layer
│   │   │   ├── job_repo.py, candidate_repo.py, ranking_repo.py, audit_repo.py
│   │   ├── routers/                   # FastAPI route handlers (all prefixed with /api)
│   │   │   ├── jobs.py                # CRUD jobs, requirements, JD bias check, audit logs
│   │   │   ├── candidates.py          # CRUD candidates, resume upload, parsed profile
│   │   │   ├── rankings.py            # POST /jobs/{id}/rank, GET /jobs/{id}/rankings
│   │   │   ├── overrides.py           # POST /rankings/{id}/override, GET weight-suggestions
│   │   │   ├── bias.py                # GET /jobs/{id}/bias-report, POST /counterfactual-test
│   │   │   ├── chat.py                # POST /jobs/{id}/chat (RAG grounded recruiter assistant)
│   │   │   └── evaluation.py          # GET /evaluation/results (ablation benchmark metrics)
│   │   ├── core/                      # Pure business logic & algorithms (NO raw DB access)
│   │   │   ├── llm/                   # Abstract LLM client, MockLLMClient, prompt templates
│   │   │   │   ├── client.py          # LLMClient ABC, MockLLMClient, ProviderFactory
│   │   │   │   ├── cache.py           # In-memory/disk SHA256 prompt caching
│   │   │   │   ├── defense.py         # Prompt injection & delimiter breakout sanitization
│   │   │   │   └── prompts/           # Jinja-free strict tag templates (v1_*.txt)
│   │   │   ├── parsing/               # Hybrid resume ingestion
│   │   │   │   ├── extractors.py      # PyMuPDF & python-docx extractors
│   │   │   │   ├── section_heuristics.py # Regex section & contact extraction
│   │   │   │   ├── date_calculator.py # Overlapping tenure, gaps, total years calculator
│   │   │   │   └── pipeline.py        # Confidence checker (rules vs. LLM fallback)
│   │   │   ├── taxonomy/              # Skill ontology graph
│   │   │   │   ├── ontology.py        # SkillOntology (synonyms, sibling 0.4, parent 0.7)
│   │   │   │   └── jd_extractor.py    # Requirement extractor & JD inclusive language checker
│   │   │   ├── embeddings/            # Semantic retrieval
│   │   │   │   ├── chunker.py         # ResumeChunker (structural bullets, location weights)
│   │   │   │   ├── encoder.py         # BiEncoder with SemanticFallbackVectorizer
│   │   │   │   ├── reranker.py        # CrossEncoderReranker (top-K snippet reranking)
│   │   │   │   └── retriever.py       # TwoStageRetriever (Bi-Encoder + Cross-Encoder)
│   │   │   ├── scoring/               # Deterministic ranking engine
│   │   │   │   ├── engine.py          # DeterministicScoringEngine (pure math scoring formulas)
│   │   │   │   ├── evidence_judge.py  # LLMEvidenceJudge (categorical verdict extraction)
│   │   │   │   └── explainer.py       # CandidateExplainer (grounded reasons & interview Qs)
│   │   │   ├── bias/                  # Fairness & EEOC safeguards
│   │   │   │   ├── blind_redactor.py  # 6-layer PII/demographic redactor
│   │   │   │   ├── adverse_impact.py  # EEOC 4/5ths Rule (80% impact ratio) monitor
│   │   │   │   ├── counterfactual.py  # Demographic swap & delta-score stability tester
│   │   │   │   └── proxy_detector.py  # Identifies zip codes, graduation years, sororities
│   │   │   ├── learning/              # Human-in-the-loop recalibration
│   │   │   │   └── weight_recalibration.py # Ridge regression with Dirichlet/Bayesian prior
│   │   │   └── evaluation/            # Ablation benchmarking harness
│   │   │       ├── baseline_ats.py    # Traditional TF-IDF keyword frequency matcher
│   │   │       ├── synthetic_data.py  # 45 synthetic resumes across 3 roles + keyword traps
│   │   │       └── benchmark.py       # NDCG@5, NDCG@10, Precision@k, MRR computation
│   │   └── services/                  # Orchestration layer (wires repositories + core algorithms)
│   │       ├── ranking_service.py     # Executes full ranking pipeline & persists run
│   │       ├── bias_service.py        # Generates audit reports & counterfactual runs
│   │       ├── override_service.py    # Records overrides & computes weight updates
│   │       ├── evaluation_service.py  # Runs benchmark comparisons
│   │       └── chat_service.py        # Grounded recruiter QA with citations
│   └── tests/                         # Full automated test suite (92 tests)
│       ├── conftest.py                # In-memory SQLite fixtures, Mock LLM fixtures
│       ├── test_phase1.py ... test_phase10_chat.py
```

---

## 3. How to Run the System

### A. Run Automated Test Suite (All 92 tests)
```powershell
cd "c:\Users\gamer\Desktop\minor proj\backend"
.\venv\Scripts\pytest -v tests
```
*(Runs in ~2.7 seconds; all tests must pass).*

### B. Launch FastAPI Backend Server (Port 8000)
```powershell
cd "c:\Users\gamer\Desktop\minor proj\backend"
.\venv\Scripts\uvicorn app.main:app --port 8000 --host 127.0.0.1
```
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### C. Launch Streamlit Recruiter Dashboard (Port 8501)
```powershell
cd "c:\Users\gamer\Desktop\minor proj\backend"
.\venv\Scripts\streamlit run streamlit_app.py
```
- Dashboard UI: `http://localhost:8501`

### D. Re-seed Demo Data (if database is cleared)
```powershell
cd "c:\Users\gamer\Desktop\minor proj\backend"
.\venv\Scripts\python scripts/seed.py
```

---

## 4. Architectural Gotchas & Critical Implementations

Keep these lessons in mind when editing or adding code:

1. **FastAPI Router Prefix is `/api`**:
   - In `backend/app/main.py`, routers are included with `prefix="/api"`.
   - Correct routes: `GET /api/jobs`, `POST /api/jobs/{id}/rank`, `POST /api/jobs/{id}/chat`, etc.
   - Do NOT query `/jobs` directly without the `/api` prefix.

2. **Order of Operations in Blind Redactor (`blind_redactor.py`)**:
   - **Crucial rule**: Always redact emails and phone numbers *before* redacting candidate names.
   - Why: If names like `John` or `Doe` are replaced first, `john.doe@email.com` becomes `[REDACTED_NAME].[REDACTED_NAME]@email.com`, breaking the email regex.

3. **Fallback Vectorizer Token Alignment (`skill_ontology.json`)**:
   - In offline or lightweight mode without PyTorch/HuggingFace downloads, `SemanticFallbackVectorizer` expands words through `backend/data/skill_ontology.json`.
   - If adding new domain skills, ensure synonyms are registered in `skill_ontology.json` so cosine similarities evaluate cleanly.

4. **AuditLog Schema Column Name**:
   - The JSON payload column in `app/models/audit_log.py` is named `detail` (singular).
   - An alias property `@property def details(self)` exists on `AuditLog` to prevent keyword argument mismatches.

5. **Sorting of Candidate Rankings**:
   - SQLAlchemy's `run.candidate_rankings` relationship is an unordered collection.
   - Always sort before returning: `sorted(run.candidate_rankings, key=lambda x: x.rank if x.rank is not None else 9999)`.

6. **Streamlit Design Constraints**:
   - The UI adheres strictly to **Flat SaaS Design**: solid backgrounds, clean borders (`1px solid #E2E8F0`), Inter typography, zero gradients, minimal box shadows.
   - Do NOT introduce colorful gradients or bubbly card designs into `streamlit_app.py`.

---

## 5. Environment & LLM Providers

Configuration is managed via Pydantic Settings in `backend/app/config.py`:
- By default, `LLM_PROVIDER=mock`, allowing the full system, parser fallbacks, evidence judging, and recruiter chat to operate instantly offline with zero API keys.
- To use live Google Gemini or OpenAI:
  1. Set `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` in `.env`.
  2. Set `GEMINI_API_KEY=...` or `OPENAI_API_KEY=...`.
  3. The `ProviderFactory` in `backend/app/core/llm/client.py` will automatically initialize the appropriate provider with fallback resilience.
