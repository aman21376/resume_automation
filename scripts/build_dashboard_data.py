"""Assemble the per-job data the review dashboard artifact embeds inline:
every job ever archived (not just today's), each with a freshly-regenerated
tailored resume AND cover letter HTML, so a job from any past day/region
stays fully viewable - critical for the Applied section, which must keep
working even after a job's original daily batch is long gone.

Everything is HTML only (no embedded PDF - that would balloon the page by
~100KB/job/day forever). Downloading is handled client-side via the
browser's native print-to-PDF on the preview iframe, which costs nothing
per job and scales indefinitely.

Cover letters are auto-generated (scripts/cover_letter_auto.py): a real
story anchor gets matched to the job by relevance, same mechanism as the
resume's bullet reordering. This is the scalable default for every job
here - a fully hand-written letter is still the better move for a specific
application the user cares enough about to ask for directly.

The tailored resume/cover-letter HTML is >90% identical across jobs (same
CSS, same candidate profile, same bullet pool just reordered/reselected),
so storing each one independently wastes enormous space as the archive
grows. Instead every resume_html/cover_letter_html is concatenated into one
shared blob and gzip-compressed together, so cross-job redundancy is
captured by gzip's shared dictionary (~15MB -> ~350KB on the full archive).
Each job keeps only byte offsets into the decompressed blob; the dashboard
template inflates it once client-side (pako) and slices per job.
"""
import base64
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive import load_all
from score_fit import load_master
from tailor_resume import tailor
from cover_letter_auto import generate as generate_cover_letter

ROOT = Path(__file__).resolve().parent.parent


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def main(today_str, out_path):
    master = load_master()
    days = load_all()

    jobs_meta = []
    blob_parts = []
    offset = 0

    def add_part(text):
        nonlocal offset
        encoded = text.encode("utf-8")
        start = offset
        offset += len(encoded)
        blob_parts.append(encoded)
        return start, len(encoded)

    for date_str, jobs in days:
        for j in jobs:
            key = f"{date_str}_{j['region']}_{slugify(j['company'])}_{slugify(j['title'])}"
            resume_html, category = tailor(j, master)
            cover_letter_html, story_id = generate_cover_letter(j, master)
            r_off, r_len = add_part(resume_html)
            c_off, c_len = add_part(cover_letter_html)
            jobs_meta.append({
                "key": key,
                "date": date_str,
                "is_new": date_str == today_str,
                "region": j["region"],
                "source": j.get("source", "indeed"),
                "title": j["title"],
                "company": j["company"],
                "location": j["location"],
                "score": j.get("score", 0),
                "confidence": "reviewed" if j.get("description") else "title_only",
                "salary_status": j.get("salary_status", "not_listed"),
                "visa_status": j.get("visa_status", "unclear"),
                "is_startup": j.get("is_startup", False),
                "posted_date": j.get("posted_date"),
                "apply_url": j["url"],
                "r_off": r_off,
                "r_len": r_len,
                "c_off": c_off,
                "c_len": c_len,
            })

    blob = b"".join(blob_parts)
    blob_b64 = base64.b64encode(gzip.compress(blob, 9)).decode("ascii")
    payload = {"blob": blob_b64, "jobs": jobs_meta}

    Path(out_path).write_text(json.dumps(payload))
    print(
        f"Wrote {len(jobs_meta)} jobs (across {len(days)} days) to {out_path} "
        f"(blob: {len(blob)} raw -> {len(blob_b64)} base64 bytes)"
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
