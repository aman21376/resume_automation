"""Build a tailored one-page resume HTML for a specific job, from master_resume.json.

Tailoring is limited to truthful emphasis changes only: which profile-summary
variant leads, which subset of the (fixed, real) skills list is ordered first
to mirror the job description's language, and the order bullets appear in
within each experience/project (most relevant to this job first). No
experience, project, education, or achievement content - and no experience
or project itself - is ever added, removed, or fabricated; those 3
experiences and 2 projects stay fixed across every application per the
candidate's requirement. Only bullet order within them changes.
"""
import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from score_fit import classify_role, load_master, CONCEPT_BANK

ROOT = Path(__file__).resolve().parent.parent


def build_skills_line(master, job_text):
    pool = master["skills_pool"]
    job_text_lower = job_text.lower()
    matched = [s for s in pool if s.lower() in job_text_lower]
    rest = [s for s in pool if s not in matched]
    ordered = matched + rest
    return ", ".join(ordered[:9])


def _bullet_relevance(bullet_text, job_text_lower):
    """Count concepts present in both the bullet and the job text - same
    concept-bank approach as fit scoring, so wording differences (e.g. JD
    says 'cross-functional teams', bullet says 'Cross-Functional
    Collaboration') still count as a match."""
    text_lower = bullet_text.lower()
    score = 0
    for phrasings in CONCEPT_BANK.values():
        if any(p in job_text_lower for p in phrasings) and any(p in text_lower for p in phrasings):
            score += 1
    return score


def _reorder_by_relevance(bullets, get_text, job_text_lower):
    """Stable-sorts bullets most-relevant-first; ties keep original order.
    Never drops or adds a bullet - same set, just reordered."""
    indexed = list(enumerate(bullets))
    indexed.sort(key=lambda pair: (-_bullet_relevance(get_text(pair[1]), job_text_lower), pair[0]))
    return [b for _, b in indexed]


def tailor(job, master=None):
    master = master or load_master()
    category = classify_role(job.get("title", ""))
    profile = master["profile_variants"].get(category, master["profile_variants"]["default"])
    job_text = f"{job.get('title','')} {job.get('description','')}"
    job_text_lower = job_text.lower()
    skills_line = build_skills_line(master, job_text)

    experience = []
    for exp in master["experience"]:
        exp2 = dict(exp)
        exp2["bullets"] = _reorder_by_relevance(
            exp["bullets"], lambda b: f"{b.get('lead','')} {b.get('text','')}", job_text_lower
        )
        experience.append(exp2)

    projects = []
    for p in master["projects"]:
        p2 = dict(p)
        p2["bullets"] = _reorder_by_relevance(p["bullets"], lambda b: b, job_text_lower)
        projects.append(p2)

    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    tmpl = env.get_template("resume_template.html.j2")
    html = tmpl.render(
        name=master["name"],
        contact=master["contact"],
        profile=profile,
        experience=experience,
        projects=projects,
        education=master["education"],
        skills_line=skills_line,
        achievements_lines=master["achievements_lines"],
        leadership_lines=master["leadership_lines"],
    )
    return html, category


if __name__ == "__main__":
    job = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"title": "Product Manager", "description": ""}
    html, category = tailor(job)
    out_path = ROOT / "output" / "preview.html"
    out_path.write_text(html)
    print(f"category={category} -> {out_path}")
