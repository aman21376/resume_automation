"""Persistent registry of job postings already surfaced to the user, so the
daily batch never shows (and the user never risks re-applying to) the same
opening twice. Keyed by (title, company, region) since Indeed/LinkedIn job
IDs and URLs aren't stable across separate searches for the same posting.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEN_PATH = ROOT / "data" / "seen_jobs.json"


def _key(job):
    return f"{job['title'].strip().lower()}|{job['company'].strip().lower()}|{job['region']}"


def load_seen():
    if not SEEN_PATH.exists():
        return {}
    return json.loads(SEEN_PATH.read_text())


def filter_unseen(jobs, seen=None):
    seen = seen if seen is not None else load_seen()
    return [j for j in jobs if _key(j) not in seen]


def dedupe_cross_source(jobs):
    """Same posting can appear from both Indeed and LinkedIn in one run;
    keep the highest-scored copy (call after scoring, before batch selection)."""
    seen_keys = set()
    out = []
    for j in sorted(jobs, key=lambda x: -x.get("score", 0)):
        k = _key(j)
        if k in seen_keys:
            continue
        seen_keys.add(k)
        out.append(j)
    return out


def mark_seen(jobs, seen=None, today=None):
    seen = seen if seen is not None else load_seen()
    today = today or date.today().isoformat()
    for j in jobs:
        k = _key(j)
        if k not in seen:
            seen[k] = {"first_seen": today, "title": j["title"], "company": j["company"], "region": j["region"], "source": j.get("source", "indeed")}
    SEEN_PATH.write_text(json.dumps(seen, indent=2, sort_keys=True))
    return seen


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "filter":
        jobs = json.load(open(sys.argv[2]))
        unseen = filter_unseen(jobs)
        print(f"{len(unseen)}/{len(jobs)} not previously seen", file=sys.stderr)
        json.dump(unseen, open(sys.argv[3], "w"), indent=2)
    elif sys.argv[1] == "mark":
        jobs = json.load(open(sys.argv[2]))
        seen = mark_seen(jobs)
        print(f"Registry now has {len(seen)} seen postings", file=sys.stderr)
