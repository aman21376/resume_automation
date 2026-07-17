"""Assemble the final Application Desk artifact HTML from the checked-in
template plus a jobs JSON payload (produced by build_dashboard_data.py).
Usage: python3 scripts/build_dashboard_html.py <jobs_json> <out_html>
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "templates" / "dashboard_template.html"


def main(jobs_json_path, out_html_path):
    payload = Path(jobs_json_path).read_text()
    payload = payload.replace("</script", "<\\/script")
    tmpl = TEMPLATE_PATH.read_text()
    out = tmpl.replace("__JOBS_JSON__", payload)
    Path(out_html_path).write_text(out)
    print(f"Wrote {len(out)} bytes to {out_html_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
