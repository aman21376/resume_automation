"""Permanent, git-tracked archive of every job ever surfaced. Unlike
output/ (ephemeral, gitignored), this is the durable record the dashboard
rebuilds from every day - so a job from any past day, in any region, can
still be shown (e.g. in the Applied section) even after its daily batch
is long gone. Stores lightweight fields only (no rendered resume HTML/PDF -
those get regenerated on demand from title+description, which are
deterministic and cheap to re-derive).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "data" / "archive"

FIELDS = [
    "region", "source", "title", "company", "location", "url",
    "description", "score", "salary_status", "visa_status", "posted_date", "category",
]


def save_day(date_str, jobs):
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE_DIR / f"{date_str}.json"
    slim = [{k: j.get(k) for k in FIELDS} for j in jobs]
    path.write_text(json.dumps(slim, indent=2, sort_keys=True))
    return path


def load_all():
    """Returns list of (date_str, jobs) tuples, oldest first."""
    if not ARCHIVE_DIR.exists():
        return []
    out = []
    for path in sorted(ARCHIVE_DIR.glob("*.json")):
        date_str = path.stem
        jobs = json.loads(path.read_text())
        out.append((date_str, jobs))
    return out


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "save":
        date_str, jobs_path = sys.argv[2], sys.argv[3]
        jobs = json.load(open(jobs_path))
        p = save_day(date_str, jobs)
        print(f"Saved {len(jobs)} jobs to {p}")
    elif sys.argv[1] == "stats":
        days = load_all()
        total = sum(len(jobs) for _, jobs in days)
        print(f"{len(days)} days archived, {total} total jobs")
        for date_str, jobs in days:
            print(f"  {date_str}: {len(jobs)} jobs")
