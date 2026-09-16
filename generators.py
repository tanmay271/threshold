import asyncio
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(name: str) -> str:
    """Check Streamlit secrets first (for cloud deploys), then the environment."""
    try:
        import streamlit as st
        return st.secrets.get(name, "") or os.getenv(name, "")
    except Exception:
        return os.getenv(name, "")


_client = None

def get_client():
    global _client
    if _client is None:
        workspace_id = _get_secret("ANTHROPIC_WORKSPACE_ID")
        _client = anthropic.AsyncAnthropic(
            api_key=_get_secret("ANTHROPIC_API_KEY"),
            default_headers={"anthropic-workspace-id": workspace_id} if workspace_id else None,
        )
    return _client

MODEL = "claude-sonnet-4-6"


def _ctx(hire: dict) -> str:
    us_person_line = f"\n- US Person (ITAR): {hire['us_person']}" if hire.get("us_person") else ""
    return (
        f"NEW HIRE PROFILE:\n"
        f"- Name: {hire['name']}\n"
        f"- Job Title: {hire['job_title']}\n"
        f"- Department: {hire['department']}\n"
        f"- Site Location: {hire['site']}\n"
        f"- Start Date: {hire['start_date']}\n"
        f"- Manager: {hire['manager']}\n"
        f"- Employment Type: {hire['employment_type']}\n"
        f"- Years of Experience: {hire['years_experience']}"
        f"{us_person_line}"
    )


async def generate_welcome_email(hire: dict) -> str:
    prompt = f"""{_ctx(hire)}

Write a warm, professional welcome email from Meridian Semiconductor addressed to this new hire.

Requirements:
- Open with "Dear {hire['name']},"
- Mention their specific role ({hire['job_title']}), site ({hire['site']}), and start date ({hire['start_date']})
- Second paragraph: reference Meridian's mission as a leading semiconductor manufacturer, the CHIPS Act tailwind, and how their role contributes
- Third paragraph: first-day logistics — where to go, what time to arrive, what to bring (ID, onboarding paperwork), parking/transit notes appropriate for {hire['site']}
- Fourth paragraph: warm close expressing excitement to have them join
- Sign off: "Warm regards, {hire['manager']}" with their title "Hiring Manager, {hire['department']}"
- Tone: warm, professional, human — not corporate-stiff
- No subject line — just the body starting with "Dear {hire['name']},"
"""
    r = await get_client().messages.create(
        model=MODEL, max_tokens=900,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text


async def generate_onboarding_plan(hire: dict) -> str:
    fab_note = (
        "Include specific cleanroom/fab safety certification milestones and EHS training checkpoints."
        if hire["department"] in ("Fab Operations", "Engineering", "Maintenance", "Quality")
        else ""
    )
    intern_note = (
        "Scope deliverables appropriately for an internship — include intern project kick-off by Day 15."
        if hire["employment_type"] == "Intern"
        else ""
    )
    prompt = f"""{_ctx(hire)}

Create a detailed 30-60-90 day onboarding plan tailored specifically to this hire's department ({hire['department']}) and role ({hire['job_title']}).

{fab_note} {intern_note}

Use exactly this structure with bold headers and bullet points:

**FIRST 30 DAYS — Foundation & Orientation**
- Week 1: [items]
- Week 2: [items]
- Week 3-4: [items]
Key Milestone: [specific 30-day goal]

**DAYS 31-60 — Integration & Contribution**
- First independent contributions
- Process shadowing opportunities
- Key relationships to establish
- Tools/systems to master
Key Milestone: [specific 60-day goal]

**DAYS 61-90 — Ownership & Demonstrated Value**
- Own a project or initiative
- Demonstrate role competency
- 90-day performance feedback session
- Peer and manager check-in
Key Milestone: [specific 90-day goal]

**SUCCESS METRICS AT 90 DAYS**
[3-4 measurable outcomes specific to this role and department]

Be specific — reference {hire['department']} processes, tools, and culture where relevant.
"""
    r = await get_client().messages.create(
        model=MODEL, max_tokens=1400,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text


async def generate_compliance_checklist(hire: dict) -> str:
    site = hire["site"]
    us_sites = {"Ridgeport NY", "Cedar Falls VT", "Austin TX"}

    site_block = ""
    if site in us_sites:
        us_status = hire.get("us_person", "Unknown")
        site_block = f"""
SITE-SPECIFIC REQUIREMENTS FOR {site.upper()} (US SITE):
- ITAR/EAR compliance training required by Day 5
- Export control awareness module required
- US Person status on file: {us_status}
- If Non-US Person: technology access restrictions briefing required; deemed export review
- Restricted Technology Access form must be signed before fab entry
"""
    elif "Dresden" in site:
        site_block = """
SITE-SPECIFIC REQUIREMENTS FOR DRESDEN (EU):
- GDPR data privacy training required by Day 3
- EU works council notification (HR action)
- German Works Constitution Act briefing
- Data processing role classification required
- IT systems must comply with EU data residency rules
"""
    elif "Singapore" in site:
        site_block = """
SITE-SPECIFIC REQUIREMENTS FOR SINGAPORE:
- MOM Employment Pass / Work Pass verification on Day 1 (original documents)
- CPF registration confirmation within 5 days of hire
- MOM regulatory briefing for foreign nationals (if applicable)
- Ministry of Manpower notification within statutory deadline
"""

    prompt = f"""{_ctx(hire)}
{site_block}

Generate a comprehensive compliance and access checklist for this new hire at {site}.

Use EXACTLY this format for every item:
- [ ] [Task description] | Responsible: [HR / IT / Manager / New Hire] | Due: [Day 1 / Week 1 / Week 2 / etc.]

Organize into these sections with bold headers:

**IDENTITY & SITE ACCESS**
[badge issuance, photo ID, facility access levels, parking pass]

**IT SYSTEMS PROVISIONING**
[laptop, email/M365, VPN, SSO, key department systems, shared drives, Slack/Teams]

**SAFETY & COMPLIANCE TRAINING**
[EHS orientation, PPE if applicable, emergency procedures, role-specific safety — include site-specific items above]

**HR ADMINISTRATIVE**
[I-9 / work authorization, Workday profile, direct deposit, benefits enrollment window, PTO accrual start, employee handbook acknowledgement]

**LEARNING & DEVELOPMENT**
[LinkedIn Learning enrollment, required Meridian Semiconductor training modules, role-specific certifications]

**{hire['department'].upper()} ROLE SETUP**
[tools, system access, team distribution lists, role-specific items for this department]

Make it comprehensive — at least 6 items per section.
"""
    r = await get_client().messages.create(
        model=MODEL, max_tokens=1800,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text


async def generate_first_week_schedule(hire: dict) -> str:
    fab_note = (
        "Day 2 must include cleanroom gowning protocol demo and EHS safety walkthrough."
        if hire["department"] in ("Fab Operations", "Engineering", "Maintenance")
        else ""
    )
    prompt = f"""{_ctx(hire)}

Create a detailed first-week (5-day) schedule for this new hire at {hire['site']}.

{fab_note}

Format each day EXACTLY like this:

**DAY 1 — Welcome & Administrative Orientation**
9:00 AM – HR Welcome Session & Paperwork (HR Conference Room)
10:00 AM – Badge Photo & Facility Access Setup (Security Office)
[continue through 5:00 PM with 1-hour lunch at 12:00 PM]

Requirements:
- Every day 9:00 AM to 5:00 PM with 1-hour lunch at 12:00 PM
- Day 1: HR orientation, I-9 paperwork, badge setup, laptop pickup, welcome lunch with {hire['manager']}
- Day 2: Site safety tour, department introduction, meet the team, system access
- Day 3: Role-specific tool training, key stakeholder intros, process overview for {hire['department']}
- Day 4: Shadow a senior team member, attend a relevant team meeting, deep-dive into core process
- Day 5: First week check-in with {hire['manager']}, review 30-day plan, end-of-week reflection
- Use specific room/location names appropriate for a semiconductor manufacturing site at {hire['site']}
- Use specific session names — not generic descriptions
- Include 15-min breaks at 10:30 AM and 3:00 PM
"""
    r = await get_client().messages.create(
        model=MODEL, max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text


async def generate_manager_briefing(hire: dict) -> str:
    site = hire["site"]
    us_sites = {"Ridgeport NY", "Cedar Falls VT", "Austin TX"}

    itar_block = ""
    if site in us_sites:
        us_status = hire.get("us_person", "Unknown")
        itar_block = f"""
⚠️ ITAR/EXPORT CONTROL — ACTION REQUIRED:
US Person Status on File: {us_status}
- Ensure export control training is completed before Day 5
- Do NOT grant access to ITAR-controlled technical data until compliance clearance confirmed
- If Non-US Person: coordinate immediately with Legal/Compliance on technology access restrictions
- Deemed export license review may be required — contact compliance@meridiansemi.example
"""

    prompt = f"""{_ctx(hire)}
{itar_block}

Write a confidential Manager Briefing Note for {hire['manager']} about this new hire.

Use this exact structure:

CONFIDENTIAL — MANAGER BRIEFING NOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
To: {hire['manager']}, {hire['department']}
From: Meridian Semiconductor Human Resources
Re: New Hire Onboarding — {hire['name']}, {hire['job_title']}
Site: {hire['site']} | Start Date: {hire['start_date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**NEW HIRE PROFILE SUMMARY**
[2-3 sentence summary: experience level, role context, what they bring to the team]

**YOUR MANAGER RESPONSIBILITIES — FIRST 30 DAYS**
[Bulleted checklist of specific manager actions with timing:
- Day 1: [action]
- Week 1: [actions]
- Week 2: [actions]
- Day 30: [formal 30-day check-in]]

**COMPLIANCE ITEMS REQUIRING YOUR ACTION**
[Specific flags based on site — especially ITAR block above if US site. If no flags, write "No outstanding compliance flags for this hire profile."]

**SUGGESTED FIRST 1-ON-1 TALKING POINTS**
1. [Specific topic — ask about career goals, not just the job]
2. [Specific topic — clarify 30-day expectations and success definition]
3. [Specific topic — understand their working style / what they need from you]

**KEY HR CONTACTS & RESOURCES**
- HR Business Partner: [site-appropriate contact placeholder]
- IT Help Desk: [site-appropriate]
- Onboarding resources: Workday > Learning > New Employee Journey

Keep it to one page equivalent. Tone: direct, action-oriented, collegial.
"""
    r = await get_client().messages.create(
        model=MODEL, max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text


async def generate_all_documents(hire: dict) -> dict:
    results = await asyncio.gather(
        generate_welcome_email(hire),
        generate_onboarding_plan(hire),
        generate_compliance_checklist(hire),
        generate_first_week_schedule(hire),
        generate_manager_briefing(hire),
        return_exceptions=True,
    )
    keys = ["welcome_email", "onboarding_plan", "compliance_checklist",
            "first_week_schedule", "manager_briefing"]
    return {
        k: (str(v) if isinstance(v, Exception) else v)
        for k, v in zip(keys, results)
    }
