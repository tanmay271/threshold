import asyncio
import time
from datetime import date, datetime

import streamlit as st
from dotenv import load_dotenv

from generators import generate_all_documents
from pdf_builder import build_pdf

load_dotenv()

ACCENT   = "#C6F135"   # electric lime
BG       = "#14171A"   # charcoal
CARD     = "#1E2226"
INK      = "#0F1113"   # for text on lime
WHITE    = "#F2F4F1"
DIM      = "#8B9296"
BORDER   = "rgba(242,244,241,0.10)"
WARN     = "#F5A524"
INFO     = "#4FC3F7"

# A simple doorway-with-arrow mark — Threshold's logomark.
DOOR_SVG = f"""
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="vertical-align:-4px;">
  <path d="M6 3v18M6 3h9a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3H6" stroke="{ACCENT}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M12.5 12h6.5m0 0-2.6-2.6M19 12l-2.6 2.6" stroke="{ACCENT}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Threshold — AI Onboarding, Done Before Day One",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif !important; }}

/* ── Base ── */
.stApp, [data-testid="stAppViewContainer"] {{ background-color: {BG} !important; }}
[data-testid="stHeader"] {{ background: transparent !important; }}
.main .block-container {{ color: {WHITE}; padding-top: 1.5rem; max-width: 1180px; }}
p, li, span, label {{ color: {WHITE}; }}
hr {{ border-color: {BORDER} !important; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{ background-color: {CARD} !important; border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {{ color: {WHITE} !important; }}

/* ── Primary button ── */
.stButton > button {{
    background-color: {ACCENT} !important;
    color: {INK} !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 15px !important;
    padding: 12px 28px !important;
    transition: transform 0.12s ease, box-shadow 0.15s ease;
}}
.stButton > button * {{ color: {INK} !important; }}
.stButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(198,241,53,0.25); }}

/* ── Download button ── */
.stDownloadButton > button {{
    background-color: transparent !important;
    color: {ACCENT} !important;
    border: 2px solid {ACCENT} !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 14px !important;
}}
.stDownloadButton > button * {{ color: {ACCENT} !important; }}
.stDownloadButton > button:hover {{
    background-color: {ACCENT} !important;
    color: {INK} !important;
}}
.stDownloadButton > button:hover * {{ color: {INK} !important; }}

/* ── Text inputs / selects ── */
.stTextInput input, [data-testid="stTextInputRootElement"], .stDateInput input {{
    background-color: {BG} !important;
    color: {WHITE} !important;
    border: 1px solid {BORDER} !important;
}}
[data-testid="stWidgetLabel"] p {{ color: {DIM} !important; font-size: 0.85rem; font-weight: 600; }}

/* ── Expander (generated doc cards) ── */
[data-testid="stExpander"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    margin-bottom: 8px;
}}
[data-testid="stExpander"] summary {{
    font-weight: 700 !important;
    font-size: 15px !important;
    font-family: 'Space Grotesk', sans-serif;
    color: {WHITE} !important;
}}

/* ── Header banner ── */
.brand-header {{
    background: linear-gradient(120deg, {CARD} 0%, #23281F 100%);
    padding: 24px 32px;
    border-radius: 14px;
    border: 1px solid {BORDER};
    border-left: 4px solid {ACCENT};
    margin-bottom: 26px;
}}

/* ── Metric card ── */
.metric-card {{
    background: {ACCENT};
    color: {INK};
    padding: 20px 16px;
    border-radius: 12px;
    text-align: center;
    margin: 8px 0;
}}

/* ── History item ── */
.hist-item {{
    background: {BG};
    border: 1px solid {BORDER};
    border-left: 3px solid {ACCENT};
    padding: 10px 14px;
    margin: 6px 0;
    border-radius: 8px;
    font-size: 12px;
    color: {WHITE};
}}

/* ── Doc content box ── */
.doc-box {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 22px 24px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.7;
    white-space: pre-wrap;
    color: {WHITE};
    max-height: 480px;
    overflow-y: auto;
}}

/* ── Success banner ── */
.ok-banner {{
    background: linear-gradient(120deg, #1B2A1C 0%, #223321 100%);
    color: {WHITE};
    padding: 16px 22px;
    border-radius: 10px;
    border-left: 4px solid {ACCENT};
    margin: 10px 0 20px 0;
    font-size: 14px;
}}

/* ── Section header ── */
.sec-hdr {{
    border-left: 4px solid {ACCENT};
    padding-left: 16px;
    margin: 30px 0 16px 0;
}}
.sec-hdr h2 {{ color: {WHITE} !important; margin: 0; }}

/* ── Step pills (progress) ── */
.step-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 20px;
    padding: 5px 14px 5px 8px; margin: 3px 6px 3px 0; font-size: 0.78rem; color: {DIM};
}}
.step-pill.done {{ border-color: {ACCENT}; color: {WHITE}; }}
.step-dot {{ width: 7px; height: 7px; border-radius: 50%; background: {DIM}; }}
.step-pill.done .step-dot {{ background: {ACCENT}; }}

::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 6px; }}
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
    st.markdown(f"""
<div style="text-align:left;padding:6px 0 16px;">
  <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:700;color:{WHITE};">{DOOR_SVG} Threshold</div>
  <div style="font-size:11px;color:{DIM};letter-spacing:2px;margin-top:2px;">AI ONBOARDING AUTOMATION</div>
</div>
""", unsafe_allow_html=True)

    st.markdown(
        f"<p style='font-size:12px;color:{DIM};line-height:1.6;'>"
        "Generates 5 customized onboarding documents in parallel with Claude. "
        "What used to take 2–3 hours now takes under 30 seconds.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if st.session_state.time_saved:
        st.markdown("""
<div class="metric-card">
  <div style="font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:700;">2.5 hrs</div>
  <div style="font-size:12px;margin-top:4px;font-weight:600;">Estimated Time Saved</div>
</div>
""", unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align:center;font-size:11px;color:{DIM};margin-top:6px;'>"
            "vs. 2–3 hours of manual HR work</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

    st.markdown(f"<div style='color:{WHITE};font-weight:700;font-size:13px;'>Recent Packets</div>",
                unsafe_allow_html=True)
    history = st.session_state.generation_history[-5:]
    if history:
        for item in reversed(history):
            st.markdown(f"""
<div class="hist-item">
  <div style="color:{ACCENT};font-weight:700;">{item['name']}</div>
  <div style="color:{DIM};font-size:11px;">{item['role']}</div>
  <div style="color:#5B6266;font-size:10px;">{item['ts']}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='color:{DIM};font-size:12px;'>No packets generated yet.</div>",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
<div style="font-size:10px;color:#5B6266;text-align:left;line-height:1.8;">
  Powered by Claude (Anthropic)<br>
  Threshold v1.0 &middot; Portfolio Demo<br>
  Fictional company &amp; synthetic data only
</div>""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="brand-header">
  <div style="display:flex;align-items:center;gap:20px;">
    <div style="flex-shrink:0;background:{BG};border:1px solid {BORDER};border-radius:12px;width:56px;height:56px;display:flex;align-items:center;justify-content:center;font-size:26px;">
      🚪
    </div>
    <div>
      <h1 style="color:{WHITE};margin:0;font-size:26px;font-weight:700;letter-spacing:-0.01em;">
        Threshold
      </h1>
      <p style="color:{DIM};margin:6px 0 0;font-size:13.5px;">
        Cross into Day One, fully prepared &mdash; 5 documents, generated in parallel, under 30 seconds.
      </p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SECTION 1: FORM ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr"><h2>New Hire Information</h2></div>',
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
            f"<div style='background:rgba(245,165,36,0.12);border-left:4px solid {WARN};"
            f"padding:8px 12px;border-radius:6px;font-size:12px;color:{WARN};"
            f"margin-top:8px;'>⚠ US Site — ITAR/EAR compliance applies</div>",
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
            f"<div style='background:rgba(79,195,247,0.10);border-left:4px solid {INFO};"
            f"padding:8px 12px;border-radius:6px;font-size:12px;color:{INFO};"
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
            (0.08, "Initializing AI generation pipeline..."),
            (0.18, "Connecting to Claude (Anthropic)..."),
            (0.28, "Generating Welcome Email in parallel..."),
            (0.42, "Generating 30-60-90 Day Plan..."),
            (0.56, "Generating Compliance Checklist..."),
            (0.70, "Generating First Week Schedule..."),
            (0.84, "Generating Manager Briefing Note..."),
            (0.94, "Compiling 5 documents..."),
        ]

        prog = prog_box.progress(0)
        for pct, msg in steps[:2]:
            prog.progress(pct)
            status_box.info(msg)
            time.sleep(0.25)

        try:
            prog.progress(0.25)
            status_box.info("Claude is generating all 5 documents simultaneously — please wait...")

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
                f"Onboarding packet for **{name}** generated successfully in under 30 seconds!"
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
        '<div class="sec-hdr"><h2>Generated Onboarding Packet</h2></div>',
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
            fname = f"Threshold_Onboarding_{safe}_{date.today().strftime('%Y%m%d')}.pdf"
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
            f"<div style='padding:10px 0;font-size:13px;color:{DIM};'>"
            "Downloads a branded PDF with cover page and all 5 documents compiled. "
            "Review before distributing to the new hire or manager.</div>",
            unsafe_allow_html=True,
        )
