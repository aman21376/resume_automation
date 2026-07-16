"""Fetch job description text from LinkedIn's public job-view pages
(no login required) for a list of job dicts with a 'url' field."""
import json
import os
import sys
import time

import requests
from bs4 import BeautifulSoup

PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or "http://127.0.0.1:37957"
CACERT = "/root/.ccr/ca-bundle.crt"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def fetch_description(url, pause=0.6):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, proxies={"https": PROXY, "http": PROXY}, verify=CACERT, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        desc_el = soup.select_one("div.show-more-less-html__markup")
        time.sleep(pause)
        return desc_el.get_text(" ", strip=True) if desc_el else ""
    except Exception as e:
        print(f"failed {url}: {e}", file=sys.stderr)
        return ""


if __name__ == "__main__":
    in_path, out_path = sys.argv[1], sys.argv[2]
    jobs = json.load(open(in_path))
    for i, j in enumerate(jobs):
        j["description"] = fetch_description(j["url"])
        if (i + 1) % 10 == 0:
            print(f"{i+1}/{len(jobs)} fetched", file=sys.stderr)
    json.dump(jobs, open(out_path, "w"), indent=2)
    print(f"Wrote {len(jobs)} jobs with descriptions to {out_path}")
