"""Build a one-page cover letter from templates/cover_letter_template.html.j2.

Unlike the resume, the body paragraphs here are not auto-generated from
master_resume.json - a cover letter's value is a genuine, specific
narrative (a real problem faced and solved, honestly connected to why
this particular role/company), which needs to be written per application,
not templated. This module just handles the consistent layout/contact
info/date/signature; the paragraphs are supplied by whoever is writing
the letter for a given job (grounded in real facts from master_resume.json,
never fabricated).
"""
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from score_fit import load_master

ROOT = Path(__file__).resolve().parent.parent


def build(job_title, company, salutation_name, paragraphs, master=None, today=None):
    master = master or load_master()
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    tmpl = env.get_template("cover_letter_template.html.j2")
    html = tmpl.render(
        name=master["name"],
        contact=master["contact"],
        date=(today or date.today()).strftime("%B %d, %Y"),
        job_title=job_title,
        company=company,
        salutation_name=salutation_name,
        paragraphs=paragraphs,
    )
    return html


if __name__ == "__main__":
    # Quick manual test
    html = build(
        "Example Role", "Example Co", "Hiring Team",
        ["This is a test paragraph.", "This is a second test paragraph."],
    )
    out_path = ROOT / "output" / "cover_letter_preview.html"
    out_path.write_text(html)
    print(f"Wrote {out_path}")
