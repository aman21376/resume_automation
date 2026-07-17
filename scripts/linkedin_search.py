"""Search LinkedIn's public (no-login) job search guest endpoint.

This hits LinkedIn's guest job-search API used for infinite scroll on the
public /jobs/search page - no authentication, read-only, same content
anyone gets browsing LinkedIn jobs logged out. Requests go through this
environment's egress proxy since direct browser access to some job sites
(e.g. Indeed) is blocked by network policy here, but LinkedIn's guest
endpoints are reachable.
"""
import json
import os
import re
import sys
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or "http://127.0.0.1:37957"
CACERT = "/root/.ccr/ca-bundle.crt"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BASE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def search(keywords, location, region, start=0, count=25, pause=1.0):
    params = {"keywords": keywords, "location": location, "start": start}
    resp = requests.get(
        BASE, params=params, headers={"User-Agent": UA},
        proxies={"https": PROXY, "http": PROXY}, verify=CACERT, timeout=20,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []
    for card in soup.select("li > div.base-card"):
        link_el = card.select_one("a.base-card__full-link")
        title_el = card.select_one("h3.base-search-card__title")
        company_el = card.select_one("h4.base-search-card__subtitle a")
        loc_el = card.select_one("span.job-search-card__location")
        date_el = card.select_one("time.job-search-card__listdate, time.job-search-card__listdate--new")
        if not (link_el and title_el):
            continue
        url = link_el.get("href", "").split("?")[0]
        jobs.append({
            "region": region,
            "source": "linkedin",
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": loc_el.get_text(strip=True) if loc_el else location,
            "url": url,
            "posted_date": date_el.get("datetime") if date_el else None,
            "job_id": "LI_" + re.sub(r"[^0-9]", "", url.rsplit("-", 1)[-1] or str(hash(url))),
        })
    time.sleep(pause)
    return jobs


if __name__ == "__main__":
    keywords = sys.argv[1]
    location = sys.argv[2]
    region = sys.argv[3]
    jobs = search(keywords, location, region)
    print(json.dumps(jobs, indent=2))
