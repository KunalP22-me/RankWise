"""RankWise — Streamlit Recruiter Dashboard.

Production Recruiter Interface for AI-Powered Semantic Resume Screening & Audit-Proof Ranking.
Connects to the FastAPI backend with clean, flat SaaS aesthetics and complete feature coverage.
"""

from datetime import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="RankWise | AI Candidate Ranking",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Flat SaaS Design System (No gradients, solid colors, clean borders, minimal shadows)
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #0f172a;
    }
    
    /* Solid flat cards */
    .saas-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    /* Metrics */
    .metric-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
    }
    .metric-label {
        color: #64748b;
        font-size: 0.80rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-number {
        color: #0f172a;
        font-size: 1.85rem;
        font-weight: 700;
        margin-top: 4px;
        font-variant-numeric: tabular-nums;
    }
    
    /* AI Badge */
    .ai-badge {
        display: inline-flex;
        align-items: center;
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        color: #0f172a;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-left: 6px;
        vertical-align: middle;
    }
    
    /* Evidence snippet box */
    .evidence-box {
        background-color: #f8fafc;
        border-left: 3px solid #2563eb;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        padding: 12px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 0.88rem;
        color: #1e293b;
        margin: 6px 0;
    }
    
    /* Status tags */
    .tag-strong { background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .tag-partial { background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .tag-none { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
</style>
""",
    unsafe_allow_html=True,
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000/api")


# Helper Functions to Query Backend API
def api_get(endpoint: str):
    """GET request to backend REST API."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        req = urllib.request.Request(url, headers={"User-Agent": "RankWise-Dashboard"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError:
        return None
    except Exception as e:
        return None


def api_post(endpoint: str, data: dict = None):
    """POST JSON request to backend REST API."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        body = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "RankWise-Dashboard"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        st.error(f"Server Error ({e.code}): {err_body}")
        return None
    except Exception as e:
        st.error(f"Request Error: {e}")
        return None


def api_delete(endpoint: str):
    """DELETE request to backend REST API."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method="DELETE")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 204)
    except Exception:
        return False


# Health Check
health = api_get("/health")
backend_online = health is not None and health.get("status") == "healthy"

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🎯 **RankWise**")
    st.caption("AI-Powered Semantic Resume Screening & Auditable Ranking")

    if backend_online:
        provider = health.get("llm_provider", "mock").upper()
        st.success(f"● Backend Connected ({provider})")
    else:
        st.error("● Backend Offline (Start with `uvicorn app.main:app --port 8000`)")

    st.markdown("---")
    menu = st.radio(
        "Navigation",
        [
            "🏠 Overview",
            "💼 Job Positions",
            "📄 Candidate Resumes",
            "🏆 Semantic Ranking",
            "⚖️ Bias & Fairness Audit",
            "💬 Recruiter Assistant",
            "📊 Evaluation Benchmarks",
            "📜 Audit Logs",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        "<small style='color: #64748b;'><b>Core Principle:</b><br/>"
        "The LLM reads and explains;<br/>deterministic code scores.</small>",
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════
# 1. OVERVIEW PAGE
# ═════════════════════════════════════════════════════════════════
if menu == "🏠 Overview":
    st.title("Recruiter Screening Operations")
    st.markdown("Welcome to **RankWise**, an explainable, bias-resistant hiring intelligence platform.")

    jobs = api_get("/jobs") or []
    total_jobs = len(jobs)
    total_candidates = sum(j.get("candidate_count", 0) for j in jobs)

    c1, c2 = st.columns(2)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""<div class="metric-container"><div class="metric-label">Active Job Roles</div>
            <div class="metric-number">{total_jobs}</div></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="metric-container"><div class="metric-label">Applicants Ingested</div>
            <div class="metric-number">{total_candidates}</div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("Active Job Positions")
    
    if jobs:
        df_jobs = pd.DataFrame(
            [
                {
                    "ID": j["id"][:8] + "...",
                    "Job Title": j["title"],
                    "Status": j["status"].capitalize(),
                    "Blind Mode": "Enabled (PII Redacted)" if j.get("blind_mode") else "Disabled",
                    "Applicants": j.get("candidate_count", 0),
                    "Created": str(j.get("created_at", ""))[:10],
                }
                for j in jobs
            ]
        )
        st.dataframe(df_jobs, use_container_width=True, hide_index=True)
    else:
        st.info("No job openings created yet. Go to **Job Positions** to add a new role or run `python scripts/seed.py`.")


# ═════════════════════════════════════════════════════════════════
# 2. JOB POSITIONS PAGE
# ═════════════════════════════════════════════════════════════════
elif menu == "💼 Job Positions":
    st.title("Job Positions & Requirements Editor")

    tab1, tab2 = st.tabs(["📋 View & Edit Positions", "➕ Create New Position"])

    with tab1:
        jobs = api_get("/jobs") or []
        if not jobs:
            st.info("No jobs found. Create one in the 'Create New Position' tab.")
        else:
            for job in jobs:
                with st.expander(f"**{job['title']}** — {job.get('candidate_count', 0)} Applicants ({job['status'].upper()})"):
                    col_l, col_r = st.columns([3, 1])
                    with col_l:
                        st.markdown(f"**Job ID:** `{job['id']}`")
                        st.markdown(f"**Blind Mode:** {'Enabled' if job.get('blind_mode') else 'Disabled'}")
                        st.markdown("**Description:**")
                        st.write(job["description"])

                        # Criteria weights
                        weights = job.get("weights") or {}
                        if weights:
                            st.markdown("**Scoring Weights:**")
                            w_df = pd.DataFrame([
                                {"Criterion": k.replace("_", " ").title(), "Weight": f"{v*100:.1f}%"}
                                for k, v in weights.items()
                            ])
                            st.dataframe(w_df, hide_index=True, use_container_width=True)

                    with col_r:
                        st.markdown("#### Tools")
                        if st.button("🔍 Extract Requirements", key=f"req_{job['id']}"):
                            with st.spinner("Extracting structured criteria with LLM..."):
                                res = api_post(f"/jobs/{job['id']}/extract-requirements")
                                if res:
                                    st.success("Extracted requirements successfully!")
                                    st.rerun()

                        if st.button("🛡️ Run JD Bias Check", key=f"bias_{job['id']}"):
                            with st.spinner("Analyzing JD for biased/exclusionary wording..."):
                                b_res = api_post(f"/jobs/{job['id']}/jd-bias-check")
                                if b_res:
                                    st.markdown(f"**Assessment:** {b_res.get('overall_assessment', '')}")
                                    for flag in b_res.get("flags", []):
                                        st.warning(f"**Flag:** '{flag.get('original_text')}' — {flag.get('issue')}\n\n*Suggestion:* '{flag.get('suggestion')}'")

                        # Weight suggestions from recruiter overrides
                        if st.button("⚖️ Check Weight Suggestions", key=f"sug_{job['id']}"):
                            sug = api_get(f"/jobs/{job['id']}/weight-suggestions")
                            if sug:
                                st.info(f"**Pattern Summary:** {sug.get('pattern_summary')}")
                                st.write("Suggested Weights:", sug.get("suggested_weights"))
                                if st.button("Accept Suggested Weights", key=f"acc_{job['id']}"):
                                    api_post(f"/jobs/{job['id']}/weight-suggestions/accept", {"weights": sug.get("suggested_weights")})
                                    st.success("Weights updated!")
                                    st.rerun()

                        if st.button("🗑️ Delete Job", key=f"del_{job['id']}", type="secondary"):
                            if api_delete(f"/jobs/{job['id']}"):
                                st.success("Job deleted.")
                                st.rerun()

    with tab2:
        st.subheader("Post a New Job Opening")
        with st.form("new_job_form"):
            title = st.text_input("Job Title", placeholder="e.g. Senior Machine Learning Engineer")
            desc = st.text_area(
                "Job Description & Requirements",
                placeholder="Paste the full job posting text including must-haves, nice-to-haves, and qualifications...",
                height=180,
            )
            blind_mode = st.toggle("Enable Blind Mode (Redacts candidate PII prior to ranking)", value=True)

            st.markdown("#### Criterion Weights (Must sum to 100%)")
            cw1, cw2, cw3, cw4 = st.columns(4)
            with cw1:
                w_must = st.slider("Must-Have Fit", 0, 100, 40, step=5)
            with cw2:
                w_nice = st.slider("Nice-To-Have Fit", 0, 100, 20, step=5)
            with cw3:
                w_exp = st.slider("Experience Fit", 0, 100, 25, step=5)
            with cw4:
                w_edu = st.slider("Education Fit", 0, 100, 15, step=5)

            total_w = w_must + w_nice + w_exp + w_edu
            if total_w != 100:
                st.warning(f"Weights sum to {total_w}%. Please adjust sliders to equal 100%.")

            submit_job = st.form_submit_button("🚀 Create Position", type="primary")
            if submit_job:
                if not title.strip() or not desc.strip():
                    st.error("Title and description are required.")
                else:
                    payload = {
                        "title": title,
                        "description": desc,
                        "blind_mode": blind_mode,
                        "weights": {
                            "must_have": round(w_must / 100.0, 2),
                            "nice_to_have": round(w_nice / 100.0, 2),
                            "experience": round(w_exp / 100.0, 2),
                            "education": round(w_edu / 100.0, 2),
                        },
                    }
                    new_job = api_post("/jobs", payload)
                    if new_job:
                        st.success(f"Job '{title}' created successfully!")
                        st.rerun()


# ═════════════════════════════════════════════════════════════════
# 3. CANDIDATE RESUMES PAGE
# ═════════════════════════════════════════════════════════════════
elif menu == "📄 Candidate Resumes":
    st.title("Candidate Resume Ingestion & Parsing")

    jobs = api_get("/jobs") or []
    if not jobs:
        st.warning("Please create a job position first.")
    else:
        job_opts = {j["title"]: j["id"] for j in jobs}
        chosen_title = st.selectbox("Select Target Job", list(job_opts.keys()))
        chosen_id = job_opts[chosen_title]

        tab1, tab2 = st.tabs(["👥 Candidate Pool", "📤 Upload Resumes"])

        with tab1:
            candidates = api_get(f"/jobs/{chosen_id}/candidates") or []
            if not candidates:
                st.info(f"No candidates uploaded yet for '{chosen_title}'.")
            else:
                st.markdown(f"**Total Candidates:** {len(candidates)}")
                cand_list = []
                for c in candidates:
                    parsed = c.get("parsed_data") or {}
                    cand_list.append({
                        "Name": parsed.get("name") or c["filename"],
                        "File": c["filename"],
                        "Experience": f"{c.get('total_experience_years', 0.0):.1f} yrs",
                        "Parse Method": c.get("parse_method", "rules").upper(),
                        "Confidence": f"{(c.get('parse_confidence') or 0.0)*100:.0f}%",
                        "Status": c.get("status", "uploaded").capitalize(),
                    })
                st.dataframe(pd.DataFrame(cand_list), use_container_width=True, hide_index=True)

        with tab2:
            st.subheader(f"Upload PDF / DOCX Resumes for '{chosen_title}'")
            uploaded_files = st.file_uploader(
                "Select Resume Files",
                type=["pdf", "docx"],
                accept_multiple_files=True,
            )

            if st.button("⚡ Ingest & Parse Resumes", type="primary"):
                if not uploaded_files:
                    st.warning("Select at least one resume file.")
                else:
                    progress = st.progress(0)
                    success_count = 0
                    for idx, f in enumerate(uploaded_files):
                        try:
                            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
                            content = f.read()
                            body = (
                                f"--{boundary}\r\n"
                                f'Content-Disposition: form-data; name="files"; filename="{f.name}"\r\n'
                                f"Content-Type: application/octet-stream\r\n\r\n"
                            ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")

                            req = urllib.request.Request(
                                f"{API_BASE_URL}/jobs/{chosen_id}/candidates",
                                data=body,
                                headers={
                                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                                    "User-Agent": "RankWise-Dashboard",
                                },
                                method="POST",
                            )
                            with urllib.request.urlopen(req) as resp:
                                if resp.status in (200, 201):
                                    success_count += 1
                        except Exception as e:
                            st.error(f"Error on {f.name}: {e}")
                        progress.progress((idx + 1) / len(uploaded_files))

                    st.success(f"Ingested {success_count}/{len(uploaded_files)} candidate resumes.")
                    st.rerun()


# ═════════════════════════════════════════════════════════════════
# 4. SEMANTIC RANKING PAGE
# ═════════════════════════════════════════════════════════════════
elif menu == "🏆 Semantic Ranking":
    st.title("Candidate Ranking & Evidence Assessment")

    jobs = api_get("/jobs") or []
    if not jobs:
        st.info("No jobs available.")
    else:
        job_opts = {j["title"]: j["id"] for j in jobs}
        chosen_title = st.selectbox("Select Position", list(job_opts.keys()))
        chosen_id = job_opts[chosen_title]

        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("Scoring: Code computes exact weighted score from verified LLM evidence verdicts, similarity, location, and recency.")
        with col2:
            if st.button("🚀 Run Semantic Ranking", type="primary"):
                with st.spinner("Executing two-stage retrieval, cross-encoder reranking, and evidence judging..."):
                    run_res = api_post(f"/jobs/{chosen_id}/rank?sync=true")
                    if run_res:
                        st.success("Ranking run completed!")
                        st.rerun()

        rankings_data = api_get(f"/jobs/{chosen_id}/rankings")
        if not rankings_data or not rankings_data.get("candidate_rankings"):
            st.info("No completed ranking run found for this position. Click 'Run Semantic Ranking' above.")
        else:
            cand_rankings = rankings_data["candidate_rankings"]
            st.markdown(f"### Ranked Leaderboard ({len(cand_rankings)} Applicants)")

            # Table display
            table_rows = []
            for cr in cand_rankings:
                final_score = cr.get("overridden_score") or cr.get("overall_score", 0.0)
                table_rows.append({
                    "Rank": f"#{cr['rank']}",
                    "Candidate": cr.get("candidate_name") or cr.get("candidate_filename", "Candidate"),
                    "Overall Fit": f"{final_score * 100:.1f}%",
                    "Must-Have": f"{(cr.get('must_have_score') or 0.0)*100:.1f}%",
                    "Nice-To-Have": f"{(cr.get('nice_to_have_score') or 0.0)*100:.1f}%",
                    "Experience": f"{(cr.get('experience_fit_score') or 0.0)*100:.1f}%",
                    "Education": f"{(cr.get('education_fit_score') or 0.0)*100:.1f}%",
                    "Overridden": "Yes" if cr.get("overridden_score") is not None else "No",
                })
            df_table = pd.DataFrame(table_rows)
            st.dataframe(df_table, use_container_width=True, hide_index=True)

            # CSV Export
            csv = df_table.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Export Leaderboard (CSV)", csv, f"rankwise_{chosen_id[:6]}_rankings.csv", "text/csv")

            # Candidate Deep Dive
            st.markdown("---")
            st.subheader("Candidate Evidence Deep Dive")
            cand_options = {
                f"Rank #{cr['rank']}: {cr.get('candidate_name') or cr.get('candidate_filename')}": cr
                for cr in cand_rankings
            }
            selected_cand_label = st.selectbox("Select Candidate for Evidence Breakdown", list(cand_options.keys()))
            selected_cr = cand_options[selected_cand_label]

            tab_a, tab_b = st.tabs(["🔍 Verified Evidence", "✍️ Recruiter Override"])

            with tab_a:
                st.markdown("#### Requirement Evidence Snippets")
                req_scores = selected_cr.get("requirement_scores") or []
                if not req_scores:
                    st.write("No granular requirement scores recorded.")
                else:
                    for req in req_scores:
                        verdict = req.get("verdict", "None")
                        v_tag = f"<span class='tag-strong'>STRONG</span>" if verdict == "Strong" else (
                            "<span class='tag-partial'>PARTIAL</span>" if verdict == "Partial" else "<span class='tag-none'>NONE</span>"
                        )
                        st.markdown(
                            f"**Requirement:** {req.get('requirement_text')} | {v_tag} (Score: {req.get('final_score', 0.0)*100:.1f}%)",
                            unsafe_allow_html=True,
                        )
                        st.caption(f"*Assessor reason:* {req.get('verdict_reason', '')}")
                        if req.get("snippet_text"):
                            st.markdown(
                                f"""<div class="evidence-box">"{req.get('snippet_text')}"<br/>
                                <small style='color: #64748b;'>Character Offsets: [{req.get('snippet_start')}, {req.get('snippet_end')}]</small></div>""",
                                unsafe_allow_html=True,
                            )
                        st.markdown("---")

            with tab_b:
                st.markdown("#### Recruiter Score Override")
                st.caption("Adjust scores with a mandatory rationale. All overrides are logged immutably.")
                with st.form("override_form"):
                    criterion = st.selectbox("Score Dimension", ["overall", "must_have", "nice_to_have", "experience", "education"])
                    new_val = st.slider("New Score", 0.0, 1.0, float(selected_cr.get("overall_score", 0.7)), step=0.01)
                    reason_cat = st.selectbox(
                        "Reason Category",
                        ["domain_expertise", "culture_fit", "incorrect_parsing", "missing_context", "other"]
                    )
                    reason_note = st.text_input("Detailed Justification Note", placeholder="e.g. Demonstrated deep open source contributions.")
                    submit_ov = st.form_submit_button("Record Override", type="primary")

                    if submit_ov:
                        ov_payload = {
                            "criterion": criterion,
                            "new_score": new_val,
                            "reason_category": reason_cat,
                            "reason_text": reason_note,
                        }
                        ov_res = api_post(f"/rankings/{selected_cr['id']}/override", ov_payload)
                        if ov_res:
                            st.success("Override recorded successfully!")
                            st.rerun()


# ═════════════════════════════════════════════════════════════════
# 5. BIAS & FAIRNESS AUDIT PAGE
# ═════════════════════════════════════════════════════════════════
elif menu == "⚖️ Bias & Fairness Audit":
    st.title("Bias Safeguards & Adverse Impact Monitoring")

    jobs = api_get("/jobs") or []
    if not jobs:
        st.info("No jobs found.")
    else:
        job_opts = {j["title"]: j["id"] for j in jobs}
        chosen_title = st.selectbox("Position for Bias Audit", list(job_opts.keys()))
        chosen_id = job_opts[chosen_title]

        report = api_get(f"/jobs/{chosen_id}/bias-report")

        if not report:
            st.info("No bias report available. Please run a ranking run first.")
        else:
            flagged = report.get("flagged", False)
            if flagged:
                st.warning("⚠️ **Fairness Notice:** One or more metrics flagged potential disparity or adverse impact.")
            else:
                st.success("✅ **Fairness Certified:** Zero adverse impact or demographic variance detected.")

            st.write(f"**Audit Summary:** {report.get('summary', '')}")

            # 4/5ths Rule
            st.subheader("1. EEOC Four-Fifths (80%) Rule Analysis")
            ai_data = report.get("adverse_impact") or {}
            groups = ai_data.get("groups") or {}
            if groups:
                ai_rows = []
                for g_name, g_info in groups.items():
                    ai_rows.append({
                        "Demographic Cohort": g_name,
                        "Applicants": g_info.get("total_applicants", 0),
                        "Shortlisted": g_info.get("shortlisted", 0),
                        "Selection Rate": f"{g_info.get('selection_rate', 0.0)*100:.1f}%",
                        "Impact Ratio (vs Max)": f"{g_info.get('impact_ratio', 1.0):.2f}",
                        "Status": "VIOLATION (<80%)" if g_info.get("adverse_impact_flag") else "PASS (>=80%)",
                    })
                st.dataframe(pd.DataFrame(ai_rows), use_container_width=True, hide_index=True)

            # Counterfactual Tests
            st.subheader("2. Counterfactual Perturbation Testing")
            st.caption("Swaps protected demographic tokens (names, pronouns, grad years) and measures score stability.")

            if st.button("🧪 Re-Run Counterfactual Tests"):
                with st.spinner("Testing counterfactual variants..."):
                    cf_data = api_post(f"/jobs/{chosen_id}/counterfactual-test")
                    if cf_data:
                        st.success(f"Tested {cf_data.get('total_tested', 0)} candidate profiles.")
                        st.json(cf_data.get("results", []))

            cf_results = report.get("counterfactual_results") or {}
            if cf_results and "results" in cf_results:
                cf_table = []
                for r in cf_results["results"]:
                    cf_table.append({
                        "Original Name": r.get("original_name"),
                        "Perturbed Variant": r.get("perturbed_name"),
                        "Original Score": f"{r.get('original_score', 0.0):.3f}",
                        "Perturbed Score": f"{r.get('perturbed_score', 0.0):.3f}",
                        "Score Delta": f"{r.get('score_delta', 0.0):.4f}",
                        "Flagged": "YES" if r.get("is_flagged") else "Invariant (PASS)",
                    })
                st.dataframe(pd.DataFrame(cf_table), use_container_width=True, hide_index=True)

            # Proxy warnings
            proxy_warnings = report.get("proxy_warnings") or []
            if proxy_warnings:
                st.subheader("3. Proxy Feature Correlation Warnings")
                for pw in proxy_warnings:
                    st.warning(f"**Feature:** {pw.get('feature')} | Correlation: {pw.get('correlation')}\n\n{pw.get('warning')}")


# ═════════════════════════════════════════════════════════════════
# 6. RECRUITER ASSISTANT CHAT
# ═════════════════════════════════════════════════════════════════
elif menu == "💬 Recruiter Assistant":
    st.title("Recruiter AI Assistant")
    st.caption("Ask questions about candidate capabilities. Answers are strictly grounded in retrieved resume evidence.")

    jobs = api_get("/jobs") or []
    if not jobs:
        st.info("No jobs available.")
    else:
        job_opts = {j["title"]: j["id"] for j in jobs}
        chosen_title = st.selectbox("Position Context", list(job_opts.keys()))
        chosen_id = job_opts[chosen_title]

        # Initialize session chat history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []

        # Display history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "citations" in msg and msg["citations"]:
                    st.markdown("**Supporting Evidence:**")
                    for cit in msg["citations"]:
                        st.markdown(
                            f"""<div class="evidence-box"><b>{cit.get('candidate_name', 'Candidate')}:</b> "{cit.get('snippet', '')}"</div>""",
                            unsafe_allow_html=True,
                        )

        # Input query
        user_query = st.chat_input("e.g. Who has production Kafka or distributed systems experience?")
        if user_query:
            st.session_state.chat_messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Searching candidate evidence snippets..."):
                    chat_resp = api_post(f"/jobs/{chosen_id}/chat", {"question": user_query})
                    if chat_resp:
                        ans = chat_resp.get("answer", "")
                        cits = chat_resp.get("cited_snippets", [])
                        st.markdown(ans)
                        if cits:
                            st.markdown("**Supporting Evidence:**")
                            for cit in cits:
                                st.markdown(
                                    f"""<div class="evidence-box"><b>{cit.get('candidate_name', 'Candidate')}:</b> "{cit.get('snippet', '')}"</div>""",
                                    unsafe_allow_html=True,
                                )
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": ans,
                            "citations": cits,
                        })


# ═════════════════════════════════════════════════════════════════
# 7. EVALUATION BENCHMARKS PAGE
# ═════════════════════════════════════════════════════════════════
elif menu == "📊 Evaluation Benchmarks":
    st.title("Evaluation Harness & Ablation Benchmarks")
    st.markdown("""
    **Research Ablation Study:** Evaluates candidate ranking across 3 distinct paradigms:
    1. **Baseline ATS:** Traditional TF-IDF keyword frequency matching.
    2. **Embeddings Only:** Bi-Encoder whole-document cosine similarity.
    3. **Full System (RankWise):** Two-Stage Semantic Retrieval + Cross-Encoder Reranking + LLM Evidence Judging.
    """)

    eval_data = api_get("/evaluation/results") or []
    if not eval_data:
        st.info("No evaluation data returned from backend.")
    else:
        role_titles = [r["job_role"] for r in eval_data]
        selected_role = st.selectbox("Select Evaluation Role", role_titles)
        role_res = next((r for r in eval_data if r["job_role"] == selected_role), eval_data[0])

        st.markdown(f"### Benchmark Metrics: `{selected_role}`")
        metrics = role_res.get("metrics", [])
        m_df = pd.DataFrame(metrics)
        st.dataframe(m_df, use_container_width=True, hide_index=True)

        # Plotly comparison chart
        fig = go.Figure()
        metric_names = [m["metric"] for m in metrics]
        fig.add_trace(go.Bar(name="Baseline ATS (TF-IDF)", x=metric_names, y=[m["baseline_ats"] for m in metrics], marker_color="#94a3b8"))
        fig.add_trace(go.Bar(name="Embeddings Only", x=metric_names, y=[m["embeddings_only"] for m in metrics], marker_color="#60a5fa"))
        fig.add_trace(go.Bar(name="RankWise Full System", x=metric_names, y=[m["full_system"] for m in metrics], marker_color="#1e40af"))

        fig.update_layout(
            barmode="group",
            title="Ablation Comparison Across Ranking Architectures",
            yaxis_title="Score (0.0 - 1.0)",
            yaxis_range=[0, 1.05],
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font_family="Inter",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Keyword Traps Breakdown
        st.markdown("---")
        st.subheader("Keyword Trap Resistance Analysis")
        st.caption("Demonstrating how keyword-stuffing exploits legacy ATS while RankWise correctly penalizes false evidence.")
        traps = role_res.get("keyword_trap_examples", [])
        if traps:
            st.dataframe(pd.DataFrame(traps), use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════════
# 8. AUDIT LOGS PAGE
# ═════════════════════════════════════════════════════════════════
elif menu == "📜 Audit Logs":
    st.title("Immutable Audit Trail")
    st.markdown("All candidate uploads, prompt hashes, score updates, and recruiter overrides are logged immutably.")

    logs = api_get("/jobs/all/audit-logs") or []
    if not logs:
        st.info("No audit logs recorded yet.")
    else:
        log_rows = []
        for l in logs:
            log_rows.append({
                "Timestamp": str(l.get("created_at", ""))[:19].replace("T", " "),
                "User": l.get("user", "system"),
                "Action": l.get("action", "").upper(),
                "Job ID": str(l.get("job_id") or "")[:8],
                "Details": json.dumps(l.get("detail") or {}, ensure_ascii=False),
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
