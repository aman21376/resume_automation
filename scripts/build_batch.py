"""Tailor + render a resume PDF for every job in the final batch, and emit a
click-through report (CSV + Markdown) for the user to work through.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

from tailor_resume import tailor
from score_fit import load_master

ROOT = Path(__file__).resolve().parent.parent


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def main(batch_path, outdir_name):
    master = load_master()
    jobs = json.load(open(batch_path))
    outdir = ROOT / "output" / outdir_name
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for j in jobs:
        html, category = tailor(j, master)
        fname_base = f"{j['region']}_{slugify(j['company'])}_{slugify(j['title'])}"
        html_path = outdir / f"{fname_base}.html"
        pdf_path = outdir / f"{fname_base}.pdf"
        html_path.write_text(html)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "render_pdf.js"), str(html_path), str(pdf_path)],
            check=True, cwd=ROOT,
        )
        rows.append({
            "region": j["region"],
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "score": j["score"],
            "category": category,
            "salary_status": j.get("salary_status", "not_listed"),
            "apply_url": j["url"],
            "resume_pdf": str(pdf_path.relative_to(ROOT)),
        })

    csv_path = ROOT / "output" / f"{outdir_name}_report.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    md_path = ROOT / "output" / f"{outdir_name}_report.md"
    with open(md_path, "w") as f:
        f.write(f"# Daily Application Batch — {len(rows)} jobs\n\n")
        for region in ["IN", "NL", "DE", "IE", "LU"]:
            region_rows = [r for r in rows if r["region"] == region]
            if not region_rows:
                continue
            f.write(f"## {region} ({len(region_rows)})\n\n")
            f.write("| Score | Title | Company | Salary | Apply | Resume |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in sorted(region_rows, key=lambda x: -x["score"]):
                f.write(f"| {r['score']} | {r['title']} | {r['company']} | {r['salary_status']} | [Apply]({r['apply_url']}) | {r['resume_pdf']} |\n")
            f.write("\n")

    print(f"Wrote {len(rows)} tailored resumes to {outdir}")
    print(f"Report: {csv_path}")
    print(f"Report: {md_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
