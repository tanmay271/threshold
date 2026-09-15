"""Quick smoke test — generates all 5 docs for a test hire and prints first 80 chars of each."""
import asyncio
from generators import generate_all_documents

TEST_HIRE = {
    "name": "Jordan Kim",
    "job_title": "Process Integration Engineer",
    "department": "Fab Operations",
    "site": "Ridgeport NY",
    "start_date": "June 2, 2025",
    "manager": "Sarah Chen",
    "employment_type": "Full-time",
    "years_experience": 5,
    "us_person": "Yes — US Person (confirmed)",
}

async def main():
    print("Generating all 5 documents in parallel...")
    docs = await generate_all_documents(TEST_HIRE)
    labels = {
        "welcome_email":        "1. Welcome Email",
        "onboarding_plan":      "2. 30-60-90 Plan",
        "compliance_checklist": "3. Compliance Checklist",
        "first_week_schedule":  "4. First Week Schedule",
        "manager_briefing":     "5. Manager Briefing",
    }
    all_ok = True
    print("\n" + "="*60)
    for key, label in labels.items():
        content = docs[key]
        ok = len(content) > 100 and not content.startswith("Error")
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        preview = content[:80].replace("\n", " ")
        print(f"[{status}] {label}")
        print(f"       {len(content)} chars | Preview: {preview}...")
        print()
    print("="*60)
    print("ALL DOCUMENTS OK" if all_ok else "SOME DOCUMENTS FAILED")

asyncio.run(main())
