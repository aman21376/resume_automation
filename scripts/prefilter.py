"""Title-only prefilter to cut obviously senior/irrelevant/internship listings
before spending a get_job_details call on them. Cheap first pass; score_fit.py
does the real scoring once full descriptions are fetched for survivors.
"""
import json
import sys

REJECT_MARKERS = [
    "senior", "sr ", "sr.", "staff", "lead ", "head of", "director", " vp", "principal",
    "intern", "internship",
    "software engineering", "software engineer",
    "qc analyst", "fraud analyst", "financial analyst", "aircraft pricing",
    "corporate action", "fundamentals analyst", "biochemical",
    "procurement & sourcing", "reporting analyst",
]

KEEP_OVERRIDE = ["associate product manager", "junior"]


def keep(title):
    t = title.lower()
    if any(o in t for o in KEEP_OVERRIDE):
        # still reject if it's an internship despite "junior" wording
        if "intern" in t:
            return False
        return True
    return not any(m in t for m in REJECT_MARKERS)


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    survivors = [j for j in jobs if keep(j["title"])]
    rejected = [j for j in jobs if not keep(j["title"])]
    print(f"kept {len(survivors)} / {len(jobs)}", file=sys.stderr)
    json.dump(survivors, open(sys.argv[2], "w"), indent=2)
