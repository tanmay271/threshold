import asyncio
import time
from datetime import date, datetime

import streamlit as st
from dotenv import load_dotenv

from generators import generate_all_documents
from pdf_builder import build_pdf

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Atlas Onboard — AI Onboarding Document Generator",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
.stApp { background-color: #FFFFFF; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: #0B1120 !important; }
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #FFFFFF !important; }

/* ── Primary button ── */
.stButton > button {
    background-color: #A855F7 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 12px 28px !important;
    transition: background-color 0.2s;
}
.stButton > button:hover { background-color: #9333EA !important; }

/* ── Download button ── */
.stDownloadButton > button {
    background-color: #0B1120 !important;
    color: #A855F7 !important;
    border: 2px solid #A855F7 !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}
.stDownloadButton > button:hover {
    background-color: #A855F7 !important;
    color: #FFFFFF !important;
}

/* ── Expander ── */
details > summary {
    font-weight: 700 !important;
    font-size: 15px !important;
    border-left: 5px solid #A855F7 !important;
    padding-left: 12px !important;
    background: #fafafa !important;
}

/* ── Header banner ── */
.brand-header {
    background: linear-gradient(120deg, #0B1120 0%, #1e1b3a 100%);
    padding: 22px 30px;
    border-radius: 10px;
    border-left: 7px solid #A855F7;
    margin-bottom: 24px;
}

/* ── Metric card ── */
.metric-card {
    background: linear-gradient(135deg, #A855F7 0%, #C084FC 100%);
    color: #FFF;
    padding: 18px 14px;
    border-radius: 10px;
    text-align: center;
    margin: 8px 0;
}

/* ── History item ── */
.hist-item {
    background: #1a1a2e;
    border-left: 3px solid #A855F7;
    padding: 9px 12px;
    margin: 6px 0;
    border-radius: 5px;
    font-size: 12px;
    color: #fff;
}

/* ── Doc content box ── */
.doc-box {
    background: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 22px 24px;
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    color: #1a1a1a;
    max-height: 480px;
    overflow-y: auto;
}

/* ── Success banner ── */
.ok-banner {
    background: linear-gradient(120deg, #0d3320 0%, #1a5432 100%);
    color: #fff;
    padding: 14px 20px;
    border-radius: 8px;
    border-left: 5px solid #4caf50;
    margin: 10px 0 20px 0;
    font-size: 14px;
}

/* ── Section header ── */
.sec-hdr {
    border-left: 5px solid #A855F7;
    padding-left: 14px;
    margin: 28px 0 14px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "documents": None,
    "hire_data": None,
    "generation_history": [],
    "time_saved": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

US_SITES = {"Ridgeport NY", "Cedar Falls VT", "Austin TX"}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="text-align:center;padding:12px 0 18px;">
  <div style="font-size:30px;font-weight:900;color:#A855F7;letter-spacing:2px;">&#9670; ATLAS</div>
  <div style="font-size:10px;color:#aaa;letter-spacing:4px;margin-top:-2px;">ONBOARD</div>
  <hr style="border:none;border-top:1px solid #A855F7;margin:14px 0 10px;">
  <div style="font-size:12px;color:#ccc;font-weight:600;letter-spacing:1px;">AI ONBOARDING AUTOMATION</div>
</div>
""", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:12px;color:#9ab;line-height:1.6;'>"
        "Generates 5 customized onboarding documents in parallel using Claude AI. "
        "What used to take 2–3 hours now takes under 30 seconds.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if st.session_state.time_saved:
        st.markdown("""
<div class="metric-card">
  <div style="font-size:32px;font-weight:900;">⏱ 2.5 hrs</div>
  <div style="font-size:12px;margin-top:4px;opacity:0.9;">Estimated Time Saved</div>
</div>
<div style="text-align:center;font-size:11px;color:#888;margin-top:6px;">
  vs. 2–3 hours of manual HR work
</div>
""", unsafe_allow_html=True)
        st.markdown("---")

    st.markdown("<div style='color:#ccc;font-weight:700;font-size:13px;'>Recent Packets</div>",
                unsafe_allow_html=True)
    history = st.session_state.generation_history[-5:]
    if history:
        for item in reversed(history):
            st.markdown(f"""
<div class="hist-item">
  <div style="color:#C084FC;font-weight:700;">{item['name']}</div>
  <div style="color:#ccc;font-size:11px;">{item['role']}</div>
  <div style="color:#666;font-size:10px;">{item['ts']}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#555;font-size:12px;'>No packets generated yet.</div>",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
<div style="font-size:10px;color:#889;text-align:center;line-height:1.8;">
  Powered by Claude (Anthropic)<br>
  Atlas Onboard v1.0 &middot; Portfolio Demo<br>
  Fictional company &amp; synthetic data only
</div>""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="brand-header">
  <div style="display:flex;align-items:center;gap:22px;">
    <div style="flex-shrink:0;font-size:40px;">
      &#9670;
    </div>
    <div>
      <h1 style="color:#fff;margin:0;font-size:22px;font-weight:800;letter-spacing:0.5px;">
        Atlas Onboard
      </h1>
      <p style="color:#c4b5fd;margin:5px 0 0;font-size:13px;">
        AI-powered onboarding packet generator &middot; 5 documents &middot; Under 30 seconds &middot; Powered by Claude
      </p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SECTION 1: FORM ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr"><h2 style="margin:0;color:#0B1120;">New Hire Information</h2></div>',
            unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    name = st.text_input("Full Name *", placeholder="e.g., Alex Johnson", key="f_name")
    job_title = st.text_input("Job Title *", placeholder="e.g., Senior Process Engineer", key="f_title")
    department = st.selectbox("Department *", [
        "Engineering", "Fab Operations", "Corporate", "IT", "Quality", "Maintenance",
    ], key="f_dept")
    site = st.selectbox("Site Location *", [
        "Ridgeport NY", "Cedar Falls VT", "Austin TX", "Singapore", "Dresden, Germany",
    ], key="f_site")
    start_date = st.date_input("Start Date *", value=date.today(), key="f_date")

with col2:
    manager = st.text_input("Manager Name *", placeholder="e.g., Sarah Chen", key="f_mgr")
    employment_type = st.selectbox("Employment Type *", [
        "Full-time", "Intern", "Apprentice", "Contractor",
    ], key="f_emp")
    years_exp = st.slider("Years of Experience", 0, 20, 3, key="f_exp")

    # ITAR — only for US sites
    us_person_str = None
    if site in US_SITES:
        st.markdown(
            "<div style='background:#fff3e0;border-left:4px solid #d97706;"
            "padding:8px 12px;border-radius:4px;font-size:12px;color:#7a3b00;"
            "margin-top:8px;'>⚠ US Site — ITAR/EAR compliance applies</div>",
            unsafe_allow_html=True,
        )
        us_person_toggle = st.toggle(
            "Is this hire a US Person for ITAR purposes?", value=True, key="f_itar"
        )
        us_person_str = (
            "Yes — US Person (confirmed)"
            if us_person_toggle
            else "No — Non-US Person (export access restrictions apply)"
        )
    else:
        st.markdown(
            f"<div style='background:#e8f4fd;border-left:4px solid #2196f3;"
            f"padding:8px 12px;border-radius:4px;font-size:12px;color:#0d47a1;"
            f"margin-top:8px;'>ℹ International site — "
            f"{'GDPR requirements apply' if 'Dresden' in site else 'MOM work pass requirements apply' if 'Singapore' in site else ''}"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("⚡ Generate Onboarding Packet", use_container_width=True)

# ── GENERATION LOGIC ──────────────────────────────────────────────────────────
if generate_btn:
    errors = []
    if not name.strip():
        errors.append("Full Name is required.")
    if not job_title.strip():
        errors.append("Job Title is required.")
    if not manager.strip():
        errors.append("Manager Name is required.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        hire_data = {
            "name": name.strip(),
            "job_title": job_title.strip(),
            "department": department,
            "site": site,
            "start_date": start_date.strftime("%B %d, %Y"),
            "manager": manager.strip(),
            "employment_type": employment_type,
            "years_experience": years_exp,
            "us_person": us_person_str,
        }

        st.markdown("---")
        status_box = st.empty()
        prog_box = st.empty()

        steps = [
            (0.08, "🔄 Initializing AI generation pipeline..."),
            (0.18, "📡 Connecting to Claude (Anthropic)..."),
            (0.28, "📝 Generating Welcome Email in parallel..."),
            (0.42, "📋 Generating 30-60-90 Day Plan..."),
            (0.56, "✅ Generating Compliance Checklist..."),
            (0.70, "📅 Generating First Week Schedule..."),
            (0.84, "📊 Generating Manager Briefing Note..."),
            (0.94, "🔧 Compiling 5 documents..."),
        ]

        prog = prog_box.progress(0)
        for pct, msg in steps[:2]:
            prog.progress(pct)
            status_box.info(msg)
            time.sleep(0.25)

        try:
            prog.progress(0.25)
            status_box.info("🤖 Claude AI generating all 5 documents simultaneously — please wait...")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            documents = loop.run_until_complete(generate_all_documents(hire_data))
            loop.close()

            for pct, msg in steps[6:]:
                prog.progress(pct)
                status_box.info(msg)
                time.sleep(0.2)

            prog.progress(1.0)
            time.sleep(0.3)
            prog_box.empty()
            status_box.empty()

            st.session_state.documents = documents
            st.session_state.hire_data = hire_data
            st.session_state.time_saved = True
            st.session_state.generation_history.append({
                "name": hire_data["name"],
                "role": f"{hire_data['job_title']} · {hire_data['department']}",
                "ts": datetime.now().strftime("%b %d, %Y %I:%M %p"),
            })

            st.success(
                f"✅ Onboarding packet for **{name}** generated successfully in under 30 seconds!"
            )
            st.rerun()

        except Exception as exc:
            prog_box.empty()
            status_box.empty()
            st.error(f"Generation failed: {exc}")

# ── SECTION 2: DOCUMENTS ──────────────────────────────────────────────────────
if st.session_state.documents:
    docs = st.session_state.documents
    hire = st.session_state.hire_data

    st.markdown("---")
    st.markdown(
        '<div class="sec-hdr"><h2 style="margin:0;color:#0B1120;">Generated Onboarding Packet</h2></div>',
        unsafe_allow_html=True,
    )

    st.markdown(f"""
<div class="ok-banner">
  <b>Packet ready for:</b> {hire['name']} &nbsp;|&nbsp;
  {hire['job_title']} &nbsp;|&nbsp;
  {hire['department']} &nbsp;|&nbsp;
  {hire['site']} &nbsp;|&nbsp;
  Starting {hire['start_date']}
</div>""", unsafe_allow_html=True)

    doc_meta = [
        ("welcome_email",        "📧",  "Personalized Welcome Email",
         "Warm welcome from the hiring manager tailored to role, site, and start date"),
        ("onboarding_plan",      "📋",  "30-60-90 Day Onboarding Plan",
         "Department-specific milestones for the first 90 days"),
        ("compliance_checklist", "✅",  "Compliance & Access Checklist",
         "Site-specific compliance, IT provisioning, and HR administrative checklist"),
        ("first_week_schedule",  "📅",  "First Week Schedule",
         "Day-by-day schedule with specific time blocks for the first 5 days"),
        ("manager_briefing",     "📊",  "Manager Briefing Note",
         "Confidential briefing for the hiring manager with action items"),
    ]

    for key, icon, title, caption in doc_meta:
        content = docs.get(key, "Document not available.")
        with st.expander(f"{icon}  {title}", expanded=False):
            st.caption(caption)

            c1, c2, _ = st.columns([1, 1, 4])
            with c1:
                if st.button("Copy text", key=f"copy_{key}"):
                    st.session_state[f"show_copy_{key}"] = True
            with c2:
                if st.session_state.get(f"show_copy_{key}"):
                    if st.button("Hide", key=f"hide_{key}"):
                        st.session_state[f"show_copy_{key}"] = False

            if st.session_state.get(f"show_copy_{key}"):
                st.code(content, language=None)
            else:
                st.markdown(
                    f'<div class="doc-box">{content}</div>',
                    unsafe_allow_html=True,
                )

    # ── Download PDF ──────────────────────────────────────────────────────────
    st.markdown("---")
    col_dl, col_info = st.columns([2, 3])
    with col_dl:
        try:
            pdf_bytes = build_pdf(hire, docs)
            safe = hire["name"].replace(" ", "_")
            fname = f"Atlas_Onboard_{safe}_{date.today().strftime('%Y%m%d')}.pdf"
            st.download_button(
                label="⬇  Download Complete Onboarding Packet (PDF)",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"PDF build error: {exc}")
    with col_info:
        st.markdown(
            "<div style='padding:10px 0;font-size:13px;color:#555;'>"
            "Downloads a branded PDF with cover page and all 5 documents compiled. "
            "Review before distributing to the new hire or manager.</div>",
            unsafe_allow_html=True,
        )
