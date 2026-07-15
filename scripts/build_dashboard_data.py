"""Assemble the per-job data (metadata + tailored resume HTML) that the
review dashboard artifact embeds inline as a JS constant.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def main(batch_path, resumes_dir_name, out_path):
    jobs = json.load(open(batch_path))
    resumes_dir = ROOT / "output" / resumes_dir_name
    payload = []
    for j in jobs:
        fname_base = f"{j['region']}_{slugify(j['company'])}_{slugify(j['title'])}"
        html_path = resumes_dir / f"{fname_base}.html"
        resume_html = html_path.read_text() if html_path.exists() else ""
        job_key = fname_base
        payload.append({
            "key": job_key,
            "region": j["region"],
            "source": j.get("source", "indeed"),
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "score": j["score"],
            "confidence": "reviewed" if j.get("description") else "title_only",
            "salary_status": j.get("salary_status", "not_listed"),
            "apply_url": j["url"],
            "resume_html": resume_html,
        })
    Path(out_path).write_text(json.dumps(payload))
    print(f"Wrote {len(payload)} jobs to {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
