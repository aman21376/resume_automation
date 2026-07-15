"""Convert a Cookie-Editor JSON export into a Playwright storageState.json."""
import json
import sys

SAME_SITE_MAP = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", None: "Lax"}


def convert(raw_path, out_path):
    raw = json.load(open(raw_path))
    cookies = []
    for c in raw:
        cookies.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "expires": -1 if c.get("session") else c.get("expirationDate", -1),
            "httpOnly": bool(c.get("httpOnly", False)),
            "secure": bool(c.get("secure", False)),
            "sameSite": SAME_SITE_MAP.get(c.get("sameSite"), "Lax"),
        })
    state = {"cookies": cookies, "origins": []}
    json.dump(state, open(out_path, "w"), indent=2)
    print(f"Wrote {len(cookies)} cookies to {out_path}")


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
