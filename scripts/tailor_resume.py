"""Build a tailored one-page resume HTML for a specific job, from master_resume.json.

Tailoring is limited to truthful emphasis changes only: which profile-summary
variant leads, and which subset of the (fixed, real) skills list is ordered
first to mirror the job description's language. No experience, project,
education, or achievement content is ever added, removed, or fabricated -
those stay fixed across every application per the candidate's requirement.
"""
import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from score_fit import classify_role, load_master

ROOT = Path(__file__).resolve().parent.parent


def build_skills_line(master, job_text):
    pool = master["skills_pool"]
    job_text_lower = job_text.lower()
    matched = [s for s in pool if s.lower() in job_text_lower]
    rest = [s for s in pool if s not in matched]
    ordered = matched + rest
    return ", ".join(ordered[:9])


def tailor(job, master=None):
    master = master or load_master()
    category = classify_role(job.get("title", ""))
    profile = master["profile_variants"].get(category, master["profile_variants"]["default"])
    job_text = f"{job.get('title','')} {job.get('description','')}"
    skills_line = build_skills_line(master, job_text)

    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    tmpl = env.get_template("resume_template.html.j2")
    html = tmpl.render(
        name=master["name"],
        contact=master["contact"],
        profile=profile,
        experience=master["experience"],
        projects=master["projects"],
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
