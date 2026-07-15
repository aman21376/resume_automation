"""Score a job listing's fit against the candidate's master resume.

Fit is scored on: role-category keyword match, seniority match (years
required vs ~2 yrs actual experience), and keyword overlap with the
resume's skill/experience/project tags. Salary is reported separately
since Indeed rarely populates compensation data - it is never used to
silently drop a listing.
"""
import json
import re
from pathlib import Path

SENIOR_TITLE_MARKERS = ["senior", "sr.", "sr ", "staff", "lead ", "head of", "director", "vp ", "principal"]
JUNIOR_TITLE_MARKERS = ["associate", "junior", "jr.", "analyst", "intern", "entry"]

ROLE_CATEGORIES = {
    "product_manager": ["product manager", "product owner", "pm "],
    "product_analyst": ["product analyst", "product data analyst"],
    "business_analyst": ["business analyst", "business analytics"],
    "growth": ["growth manager", "growth lead", "growth analyst", "growth associate"],
}

MAX_YEARS_REQUIRED = 4  # candidate has ~2 years full-time + internships


def _extract_years_required(text):
    years = [int(y) for y in re.findall(r"(\d+)\s*\+?\s*(?:-|to)?\s*\d*\s*years?", text.lower())]
    return min(years) if years else None


def classify_role(title):
    t = title.lower()
    for category, markers in ROLE_CATEGORIES.items():
        if any(m in t for m in markers):
            return category
    return "default"


def score_job(job, skills_pool, all_keywords):
    """job: dict with title, company, location, description (may be short from search, or full from get_job_details)."""
    title = job.get("title", "")
    desc = job.get("description", "") or ""
    text = f"{title} {desc}".lower()

    reasons = []
    score = 0

    # Seniority gate
    years_required = _extract_years_required(desc)
    title_is_senior = any(m in title.lower() for m in SENIOR_TITLE_MARKERS)
    title_is_junior = any(m in title.lower() for m in JUNIOR_TITLE_MARKERS)

    if title_is_senior and not title_is_junior:
        score -= 40
        reasons.append("Title reads senior/staff/lead — above current ~2yr experience level")
    if years_required and years_required > MAX_YEARS_REQUIRED:
        score -= 40
        reasons.append(f"JD asks for {years_required}+ years — above current experience")
    elif years_required and years_required <= MAX_YEARS_REQUIRED:
        score += 15
        reasons.append(f"JD asks for {years_required}+ years — within range")

    # Role category match
    category = classify_role(title)
    if category != "default":
        score += 20
        reasons.append(f"Matches target role category: {category}")

    # Keyword overlap
    matched_skills = [s for s in skills_pool if s.lower() in text]
    matched_kw = [k for k in all_keywords if k.lower() in text]
    score += min(len(matched_skills) * 4, 30)
    score += min(len(matched_kw) * 2, 20)
    if matched_skills:
        reasons.append(f"Matched skills: {', '.join(matched_skills[:6])}")

    # Salary
    comp = job.get("compensation")
    salary_status = "listed" if comp and comp not in ("None", "N/A", None) else "not_listed"

    return {
        "score": score,
        "category": category,
        "reasons": reasons,
        "salary_status": salary_status,
        "matched_skills": matched_skills,
        "years_required": years_required,
    }


def load_master():
    root = Path(__file__).resolve().parent.parent
    with open(root / "data/master_resume.json") as f:
        return json.load(f)


def all_keywords_from_master(master):
    kws = set()
    for exp in master["experience"]:
        kws.update(exp.get("keywords", []))
    for p in master["projects"]:
        kws.update(p.get("keywords", []))
    return kws


if __name__ == "__main__":
    import sys
    master = load_master()
    skills_pool = master["skills_pool"]
    all_kw = all_keywords_from_master(master)
    jobs = json.load(open(sys.argv[1]))
    scored = []
    for j in jobs:
        s = score_job(j, skills_pool, all_kw)
        scored.append({**j, **s})
    scored.sort(key=lambda x: -x["score"])
    print(json.dumps(scored, indent=2))
