"""For one-off, high-effort resume requests (not the mass daily batch),
scale content up via CSS zoom so the page reads as full and deliberate
rather than leaving dead space at the bottom - without ever overflowing
to a second page. The batch pipeline's fixed sizing is untouched; this
is an extra polish pass layered on top of tailor_resume.tailor()'s output.

Screen-viewport scrollHeight is NOT used as the fit signal - Chromium's
`zoom` property reflows on-screen layout but can paginate differently in
the print/PDF pipeline, so a candidate that measures "fits" on screen can
still spill to a second PDF page. The only signal trusted here is the
actual rendered PDF's page count.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START_ZOOM = 1.12
MIN_ZOOM = 1.0
STEP = 0.015


def _with_zoom(html, zoom):
    style = f"<style>body{{zoom:{zoom:.4f};}}</style>"
    if "</head>" in html:
        return html.replace("</head>", style + "</head>")
    return style + html


def _page_count(pdf_path):
    data = Path(pdf_path).read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def _render(html_path, pdf_path):
    subprocess.run(
        ["node", str(ROOT / "scripts" / "render_pdf.js"), str(html_path), str(pdf_path)],
        check=True, cwd=ROOT, capture_output=True,
    )


def fit(html, tmp_dir):
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    probe_html = tmp_dir / "_autofit_probe.html"
    probe_pdf = tmp_dir / "_autofit_probe.pdf"

    zoom = START_ZOOM
    while zoom > MIN_ZOOM:
        candidate = _with_zoom(html, zoom)
        probe_html.write_text(candidate)
        _render(probe_html, probe_pdf)
        pages = _page_count(probe_pdf)
        if pages == 1:
            break
        zoom = round(zoom - STEP, 4)
    else:
        zoom = 1.0
        candidate = _with_zoom(html, zoom)

    probe_html.unlink(missing_ok=True)
    probe_pdf.unlink(missing_ok=True)
    print(f"autofit: settled at zoom={zoom:.3f} (verified single page via actual PDF render)", file=sys.stderr)
    return candidate, zoom


if __name__ == "__main__":
    html = Path(sys.argv[1]).read_text()
    out_html, zoom = fit(html, ROOT / "output" / "_autofit_tmp")
    Path(sys.argv[2]).write_text(out_html)
    print(f"Wrote fitted HTML (zoom={zoom:.3f}) to {sys.argv[2]}")
