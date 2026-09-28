#!/usr/bin/env python3
"""
Add a link to the commercial insurance study on every calculator page.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STUDY_LINK = '<p style="margin-top:0.75rem;font-size:0.9rem">📊 <a href="/commercial-insurance-costs-by-state/">See how your state compares — 50-state cost analysis</a></p>'

SKIP = {
    "index.html",
    "about/index.html",
    "contact/index.html",
    "privacy/index.html",
    "terms/index.html",
    "press/index.html",
    "how-it-works/index.html",
    "commercial-insurance-costs-by-state/index.html",
}

DETAILS_CLOSE = re.compile(r'(</details>\s*)', re.IGNORECASE)


def patch(path):
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"error: {e}"

    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if rel in SKIP:
        return None

    if 'See how your state compares' in content:
        return None

    match = DETAILS_CLOSE.search(content)
    if not match:
        return "no-details"

    insert_at = match.end()
    content = content[:insert_at] + STUDY_LINK + "\n" + content[insert_at:]
    path.write_text(content, encoding="utf-8")
    return "added study link"


def main():
    patched = []
    errors = []
    for p in sorted(ROOT.rglob("*.html")):
        if ".git" in p.parts:
            continue
        result = patch(p)
        rel = p.relative_to(ROOT)
        if result is None:
            continue
        if isinstance(result, str) and (result.startswith("error") or result == "no-details"):
            errors.append((rel, result))
        else:
            patched.append(rel)

    print(f"\n=== PATCHED {len(patched)} FILES ===")
    for f in patched:
        print(f"  ✓ {f}")
    if errors:
        print(f"\n=== ISSUES ({len(errors)}) ===")
        for f, e in errors:
            print(f"  ⚠ {f}: {e}")


if __name__ == "__main__":
    main()
