"""Score a job listing's fit against the candidate's master resume.

Fit is scored on: role-category match, seniority match (years required vs
~2 yrs actual experience), and concept overlap with the resume's
skills/experience/projects. Salary is reported separately since Indeed
rarely populates compensation data - it is never used to silently drop a
listing.

Matching is concept-based, not exact-phrase: a JD saying "agile
methodologies" or "cross-functional teams" should count toward the same
underlying skill as the resume's "Cross-Functional Collaboration" even
though the wording differs. Each concept lists the phrasings/synonyms a
JD is likely to use; a hit on any of them counts once per concept.
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

# Concept -> phrasings/synonyms a JD might use for that concept. One hit per
# concept counts, regardless of how many synonyms match, so this rewards
# breadth of genuine overlap rather than repeating the same idea.
CONCEPT_BANK = {
    "product_strategy": ["product strategy", "product roadmap", "roadmap", "product vision", "product direction"],
    "experimentation": ["a/b test", "a/b testing", "ab test", "experimentation", "experiment"],
    "stakeholder_mgmt": ["stakeholder management", "stakeholder", "cross-functional", "cross functional"],
    "data_driven": ["data-driven", "data driven", "data analytics", "analytics", "data analysis", "data-informed"],
    "agile": ["agile", "scrum", "sprint"],
    "gtm": ["go-to-market", "go to market", "gtm", "product launch", "launch"],
    "ai_ml": ["machine learning", "artificial intelligence", " ai ", "llm", "prompt engineering", "genai", "ml "],
    "user_research": ["user research", "customer research", "user interviews", "customer interviews", "user behaviour", "user behavior"],
    "business_analysis": ["business analysis", "requirements gathering", "user stories", "kpi", "business requirements"],
    "sql_python": [" sql", "python"],
    "growth_metrics": ["growth", "conversion", "funnel", "retention", "engagement", "cro "],
    "marketplace_ecommerce": ["marketplace", "e-commerce", "ecommerce", "b2b", "b2c"],
    "brand_partnerships": ["brand management", "brand partnership", "category management", "vendor management", "partner management"],
    "communication": ["communication skills", "written and verbal", "presentation"],
}


def _extract_years_required(text):
    years = [int(y) for y in re.findall(r"(\d+)\s*\+?\s*(?:-|to)?\s*\d*\s*years?", text.lower())]
    return min(years) if years else None


def classify_role(title):
    t = title.lower()
    for category, markers in ROLE_CATEGORIES.items():
        if any(m in t for m in markers):
            return category
    return "default"


def score_job(job, skills_pool=None, all_keywords=None):
    """job: dict with title, company, location, description (may be empty if not yet fetched)."""
    title = job.get("title", "")
    desc = job.get("description", "") or ""
    text = f" {title} {desc} ".lower()
    has_desc = bool(desc.strip())

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
        score += 20
        reasons.append(f"JD asks for {years_required}+ years — within range")

    # Role category match (from title alone, so this applies even without a JD)
    category = classify_role(title)
    if category != "default":
        score += 20
        reasons.append(f"Matches target role category: {category}")

    # Concept overlap - one hit per concept, not per synonym
    matched_concepts = [
        concept for concept, phrasings in CONCEPT_BANK.items()
        if any(p in text for p in phrasings)
    ]
    score += min(len(matched_concepts) * 5, 45)
    if matched_concepts:
        reasons.append(f"Matched concepts: {', '.join(matched_concepts)}")
    if not has_desc:
        reasons.append("No JD fetched yet — score is title/category only, treat as unverified")

    score = max(0, min(100, score))

    # Salary
    comp = job.get("compensation")
    salary_status = "listed" if comp and comp not in ("None", "N/A", None) else "not_listed"

    return {
        "score": score,
        "category": category,
        "reasons": reasons,
        "salary_status": salary_status,
        "matched_concepts": matched_concepts,
        "years_required": years_required,
        "has_desc": has_desc,
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
    jobs = json.load(open(sys.argv[1]))
    scored = []
    for j in jobs:
        s = score_job(j)
        scored.append({**j, **s})
    scored.sort(key=lambda x: -x["score"])
    print(json.dumps(scored, indent=2))
