"""Title-only prefilter to cut obviously senior/irrelevant/internship listings
before spending a get_job_details call on them. Cheap first pass; score_fit.py
does the real scoring once full descriptions are fetched for survivors.
"""
import json
import re
import sys

REJECT_MARKERS = [
    "senior", "sr ", "sr.", "staff", "lead ", "head of", "director", " vp", "principal",
    "internship",
    "software engineering", "software engineer",
    "qc analyst", "fraud analyst", "financial analyst", "aircraft pricing",
    "corporate action", "fundamentals analyst", "biochemical",
    "procurement & sourcing", "reporting analyst",
]

# Matched with a word boundary, unlike REJECT_MARKERS, since a plain substring
# check on "intern" also rejects "International" (e.g. JPMorganChase's
# "International Private Bank ... Product Owner" posting).
INTERN_RE = re.compile(r"\bintern\b")

KEEP_OVERRIDE = ["associate product manager", "junior"]


def keep(title):
    t = title.lower()
    if any(o in t for o in KEEP_OVERRIDE):
        # still reject if it's an internship despite "junior" wording
        if INTERN_RE.search(t):
            return False
        return True
    if INTERN_RE.search(t):
        return False
    return not any(m in t for m in REJECT_MARKERS)


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    survivors = [j for j in jobs if keep(j["title"])]
    rejected = [j for j in jobs if not keep(j["title"])]
    print(f"kept {len(survivors)} / {len(jobs)}", file=sys.stderr)
    json.dump(survivors, open(sys.argv[2], "w"), indent=2)
