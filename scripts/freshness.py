"""Filter out postings old enough to likely be closed already. LinkedIn gives
an ISO datetime; Indeed search results give a human date string like
"July 15, 2026" via the 'Posted on' field. Missing/unparseable dates are
kept but flagged, since we can't penalize what we can't read.
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

MAX_AGE_DAYS = 21  # postings older than ~3 weeks are meaningfully more likely closed

MONTH_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})"
)


def parse_posted_date(job, today=None):
    today = today or date.today()
    raw = job.get("posted_date")
    if not raw:
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        pass
    m = MONTH_RE.search(raw)
    if m:
        try:
            return datetime.strptime(f"{m.group(1)} {m.group(2)}, {m.group(3)}", "%B %d, %Y").date()
        except ValueError:
            return None
    return None


def is_fresh(job, today=None, max_age_days=MAX_AGE_DAYS):
    today = today or date.today()
    posted = parse_posted_date(job, today)
    if posted is None:
        return True  # unknown date - don't penalize, just can't verify
    return (today - posted).days <= max_age_days


def filter_fresh(jobs, today=None, max_age_days=MAX_AGE_DAYS):
    today = today or date.today()
    fresh, stale = [], []
    for j in jobs:
        (fresh if is_fresh(j, today, max_age_days) else stale).append(j)
    return fresh, stale


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    fresh, stale = filter_fresh(jobs)
    print(f"{len(fresh)}/{len(jobs)} within {MAX_AGE_DAYS} days, {len(stale)} dropped as likely closed", file=sys.stderr)
    json.dump(fresh, open(sys.argv[2], "w"), indent=2)
