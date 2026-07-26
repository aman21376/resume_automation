"""Score a job listing's fit against the candidate's master resume.

Fit is scored on: role-category match, seniority match (years required vs
~1.5 yrs actual experience - 1 year full-time + 9 months part-time/internship),
concept overlap with the resume's skills/experience/projects, and an extra
bonus for direct domain expertise (e-commerce/marketplace, AI/ML product
work, brand/category management - the candidate's actual day job at Meesho,
not just adjacent keyword overlap). Salary is reported separately since
Indeed rarely populates compensation data - it is never used to silently
drop a listing.

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

MAX_YEARS_REQUIRED = 1.5  # candidate has 1 year full-time + 9 months part-time/internship (~1.5-1.75 yrs combined)

# Domains the candidate has direct, hands-on expertise in (Meesho social
# commerce marketplace, AI Services callbot work, Branded Health & Wellness
# category/brand partnerships) - matches on these count extra on top of the
# normal concept-overlap score, since a JD hitting one of these isn't just a
# generic keyword overlap, it's the candidate's actual day job.
CORE_DOMAIN_CONCEPTS = {"marketplace_ecommerce", "ai_ml", "brand_partnerships", "fmcg_cpg"}

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
    "brand_partnerships": ["brand management", "brand partnership", "category management", "vendor management", "partner management", "brand onboarding", "exclusive partnership", "licensing", "licensor"],
    "fmcg_cpg": ["fmcg", "cpg", "consumer goods", "consumer packaged goods"],
    "process_coordination": ["coordinat", "timeline", "project management", "approval process", "process improvement"],
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
        reasons.append("Title reads senior/staff/lead — above current ~1.5yr experience level")
    if years_required and years_required > 2:
        score -= 40
        reasons.append(f"JD asks for {years_required}+ years — above current experience")
    elif years_required == 2:
        score -= 10
        reasons.append("JD asks for 2+ years — a stretch above current ~1.5yr experience")
    elif years_required == 1:
        score += 25
        reasons.append("JD asks for 1+ years — exact match for current experience")
    elif years_required == 0:
        score += 15
        reasons.append("JD asks for 0+ years — within range but below current experience")

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

    # Core domain bonus - e-commerce/marketplace, AI/ML product work, and
    # brand/category/partnership management are the candidate's actual
    # day-to-day expertise at Meesho, not just adjacent keyword overlap.
    core_matches = [c for c in matched_concepts if c in CORE_DOMAIN_CONCEPTS]
    if core_matches:
        score += min(len(core_matches) * 8, 24)
        reasons.append(f"Strong domain alignment (direct expertise): {', '.join(core_matches)}")
    if not has_desc:
        # Unreviewed jobs are capped low so a genuinely-matched, JD-reviewed
        # role always outranks a title-only guess of the same category.
        score = min(score, 15)
        reasons.append("No JD fetched yet — score capped, treat as unverified")

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
