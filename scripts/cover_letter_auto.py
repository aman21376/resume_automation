"""Auto-generate a job-matched cover letter for the daily dashboard.

Every job gets a real, honest personal-narrative paragraph - not an
auto-summary of the resume. A fixed library of story anchors
(data/cover_letter_stories.json), each a genuine account of something
already on the resume, gets matched to the job the same way resume
bullets are reordered: by concept-bank overlap with the JD text. The
best-matching anchor leads; the opening/closing are templated around it.

This is the scalable default for every job in the dashboard. A fully
hand-written letter (like the one built for the Ferrero application) is
still the better choice when the user cares enough about a specific
application to ask for one directly - this auto path exists so every
job has *something* genuine rather than nothing.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cover_letter import build
from score_fit import CONCEPT_BANK

ROOT = Path(__file__).resolve().parent.parent
STORIES_PATH = ROOT / "data" / "cover_letter_stories.json"


def load_stories():
    return json.loads(STORIES_PATH.read_text())


def _tag_active(tag, text_lower):
    phrasings = CONCEPT_BANK.get(tag, [])
    return any(p in text_lower for p in phrasings)


def pick_story(job_text, stories=None):
    stories = stories if stories is not None else load_stories()
    text_lower = job_text.lower()
    scored = []
    for i, s in enumerate(stories):
        score = sum(1 for t in s["tags"] if _tag_active(t, text_lower))
        scored.append((score, -i, s))  # -i keeps earlier stories as tiebreak
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2]


def generate(job, master=None, stories=None):
    job_title = job.get("title", "")
    company = job.get("company", "")
    job_text = f"{job_title} {job.get('description', '')}"
    story = pick_story(job_text, stories)

    story_para = story["paragraph"].replace("{{company}}", company).replace("{{job_title}}", job_title)

    opening = (
        f"I'm writing to apply for the {job_title} role at {company}. "
        f"I currently work in a product capacity at Meesho, one of India's largest social commerce marketplaces, "
        f"and the parts of your job description that stood out to me are exactly where my day-to-day work overlaps most."
    )
    closing = (
        f"I'd welcome the chance to talk through how this experience translates to your team's work. "
        f"Thank you for considering my application — I've attached my resume and would be glad to share anything else that's useful."
    )

    paragraphs = [opening, story_para, closing]
    html = build(job_title, company, f"{company} Hiring Team", paragraphs, master=master)
    return html, story["id"]


if __name__ == "__main__":
    job = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"title": "Product Manager", "company": "Example Co", "description": ""}
    html, story_id = generate(job)
    out_path = ROOT / "output" / "cover_letter_auto_preview.html"
    out_path.write_text(html)
    print(f"story={story_id} -> {out_path}")
