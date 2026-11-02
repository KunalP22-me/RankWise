# RankWise: Project State & Implementation Checklist

**Last Updated:** Current Session (All Phases 1–13 Complete & Tested)  
**Total Automated Tests:** 92 / 92 Passed (100%)  
**Backend Framework:** FastAPI 0.115 + SQLAlchemy 2.0 (SQLite WAL Mode)  
**Frontend Framework:** Streamlit 1.39 (Pure Flat SaaS Architecture)

---

## 1. Phase Completion Status

| Phase | Description | Status | Test Suite File | Passed |
|---|---|:---:|---|:---:|
| **Phase 1** | Database Models, Repositories & Base Schemas | ✅ Complete | `tests/test_phase1.py` | 22/22 |
| **Phase 2** | Abstract LLM Client, Mocking & Prompt Injection Defense | ✅ Complete | `tests/test_phase2_llm.py` | 12/12 |
| **Phase 3** | Hybrid Resume Parser & Tenure Calculator | ✅ Complete | `tests/test_phase3_parser.py` | 11/11 |
| **Phase 4** | JD Understanding & Hierarchical Skill Ontology | ✅ Complete | `tests/test_phase4_jd.py` | 10/10 |
| **Phase 5** | Semantic Chunker, Bi-Encoder & Cross-Encoder | ✅ Complete | `tests/test_phase5_retrieval.py` | 4/4 |
| **Phase 6** | Deterministic Scoring Engine & Grounded Explainer | ✅ Complete | `tests/test_phase6_ranking.py` | 10/10 |
| **Phase 7** | Bias Safeguards, Blind Mode & Adverse Impact Monitor | ✅ Complete | `tests/test_phase7_bias.py` | 9/9 |
| **Phase 8** | Recruiter Overrides & Ridge Weight Recalibration | ✅ Complete | `tests/test_phase8_overrides.py` | 4/4 |
| **Phase 9** | Evaluation Benchmark Harness & Adversary Traps | ✅ Complete | `tests/test_phase9_evaluation.py` | 7/7 |
| **Phase 10** | Grounded Recruiter Chat Assistant with Citations | ✅ Complete | `tests/test_phase10_chat.py` | 3/3 |
| **Phase 11** | Demo Data Seeding Script (`scripts/seed.py`) | ✅ Complete | Executed in `rankwise.db` | N/A |
| **Phase 12** | Streamlit Recruiter Dashboard (8 SaaS Views) | ✅ Complete | Manually & API Verified | N/A |
| **Phase 13** | Architecture Documentation & Quickstart | ✅ Complete | Root `README.md` | N/A |

---

## 2. API Endpoint Route Map

All API endpoints are hosted on port 8000 under the prefix `/api`:

### System
- `GET /api/health` — Returns status, version, and active LLM provider.

### Job Management
- `POST /api/jobs` — Create new job requisition.
- `GET /api/jobs` — List all active job requisitions.
- `GET /api/jobs/{id}` — Fetch specific job details.
- `POST /api/jobs/extract-requirements` — LLM-driven requirement extraction from raw text.
- `POST /api/jobs/check-bias` — Scans JD text for gendered or ageist exclusionary language.
- `GET /api/jobs/{id}/audit-log` — Fetch immutable audit trail for a specific position.
- `GET /api/jobs/all/audit-logs` — Fetch global audit events across all positions.

### Candidate Management
- `POST /api/candidates/upload` — Multipart resume upload (PDF/DOCX) with hybrid parsing.
- `GET /api/candidates` — List all candidates with parsed summaries.
- `GET /api/candidates/{id}` — Fetch full candidate profile and raw resume text.

### Ranking & Scoring Engine
- `POST /api/jobs/{id}/rank` — Execute two-stage retrieval, evidence judging, and deterministic scoring.
- `GET /api/jobs/{id}/rankings` — Fetch the latest ranked leaderboard for a job.
- `GET /api/ranking-runs/{id}/status` — Poll the progress/status of an async ranking run.

### Human-in-the-Loop & Recalibration
- `POST /api/rankings/{id}/override` — Apply recruiter override (requires written justification).
- `GET /api/jobs/{id}/weight-suggestions` — Ridge regression suggestions for requirement weights based on overrides.
- `POST /api/jobs/{id}/weight-suggestions/accept` — Apply suggested recalibrated weights.

### Bias & Adverse Impact Auditing
- `GET /api/jobs/{id}/bias-report` — EEOC 4/5ths Rule selection parity metrics across demographic groups.
- `POST /api/jobs/{id}/counterfactual-test` — Perturbs candidate names/pronouns and verifies 0.00 score drift.

### Grounded Recruiter Assistant
- `POST /api/jobs/{id}/chat` — Recruiter Q&A grounded strictly in candidate resume chunks and rankings.

### Evaluation & Benchmarks
- `GET /api/evaluation/results` — Runs comparative ablation between Baseline ATS, Embeddings-Only, and RankWise Full System.

---

## 3. Database Schema Overview (`rankwise.db`)

- **`jobs`**: `id`, `title`, `description`, `status`, `requirements_json`, `weights`, `bias_check_results`, `blind_mode`, timestamps.
- **`candidates`**: `id`, `name`, `email`, `phone`, `years_experience`, `skills`, `education_level`, `parsed_data`, `blind_parsed_data`, `demographic_metadata`.
- **`candidate_resumes`**: `id`, `candidate_id`, `filename`, `file_type`, `file_size`, `raw_text`, `parsed_confidence`, `parser_used`.
- **`ranking_runs`**: `id`, `job_id`, `status`, `total_candidates`, `model_info`, `weights_snapshot`.
- **`candidate_rankings`**: `id`, `ranking_run_id`, `candidate_id`, `rank`, `overall_score`, `must_have_score`, `nice_to_have_score`, `experience_score`, `education_score`, `requirement_verdicts`, `evidence_snippets`, `explanation`.
- **`recruiter_overrides`**: `id`, `candidate_ranking_id`, `original_rank`, `new_rank`, `original_score`, `new_score`, `reason`, `recruiter_id`.
- **`audit_logs`**: `id`, `entity_type`, `entity_id`, `action`, `actor`, `detail`, `timestamp`.

---

## 4. Potential Enhancements & Next Steps for Tomorrow

If you or the user wish to extend the project further:
1. **Containerization**: Add a `Dockerfile` and `docker-compose.yml` to bundle the backend and dashboard in a single command.
2. **PDF Report Export**: Add an endpoint/button in Streamlit to export an audit-ready compliance PDF for EEOC recordkeeping.
3. **Webhook Integration**: Add notifications (e.g., Slack or email) when an adverse impact violation is detected or when a ranking run finishes.
4. **Live Provider Testing**: Plug in a live Gemini or OpenAI API key into `.env` and verify seamless transition from `MockLLMClient` to real neural LLMs.
