---
description: RankWise AI Architecture & UI Design Rules
globs: ["**/*"]
---

# RankWise Core Architectural & Behavioral Guidelines

When modifying or extending the RankWise codebase, always observe the following rules:

## 1. The Core Scoring Invariant
- **The LLM reads and explains; deterministic code scores.**
- Never ask the LLM to generate, estimate, or assign a numeric candidate ranking score.
- The LLM's role is strictly limited to extracting structured information, judging evidence snippets categorically (`Strong`, `Partial`, `None`), and generating grounded natural language explanations.
- All numbers and rankings MUST be computed strictly by deterministic Python algorithms in `backend/app/core/scoring/`.

## 2. Frontend Constraints
- The frontend is built strictly with **Streamlit** (at `backend/streamlit_app.py` or root `streamlit_app.py`).
- Maintain a **Flat SaaS Design aesthetic**:
  - Solid neutral colors (`#0F172A`, `#1E293B`, `#F8FAFC`, `#FFFFFF`, `#E2E8F0`).
  - No decorative gradients anywhere.
  - Clean card borders (`1px solid #E2E8F0`), small border radius (`6px` to `8px`).
  - Inter typography and tabular figures for numbers.
  - Evidence badges with citations for every score component.

## 3. API Conventions
- All backend routes in FastAPI are mounted under the prefix `/api` (e.g., `/api/jobs`, `/api/health`).
- All state changes (ranking runs, overrides, job modifications) must write an entry to `audit_logs`.

## 4. Testing
- Keep the test suite green at all times (`backend/venv/Scripts/pytest -v backend/tests`).
- When writing tests, use the fixtures in `backend/tests/conftest.py` (in-memory SQLite session and mock LLM).
