#!/usr/bin/env python3
"""
Add byline to calculator pages that don't have one.
Handles the case where H1 is inside a div/box with no following <p>.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BYLINE = '<p style="color:#777;font-size:.85rem;margin-bottom:1rem">By Emiliano · Last updated 2026-09-27</p>'

# Match <h1>...</h1> at the start of a line (indented), regardless of what follows
H1_REGEX = re.compile(
    r'(\n[ \t]*)(<h1[^>]*>.*?</h1>)',
    re.DOTALL
)


def patch(path):
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"error: {e}"

    rel_str = str(path.relative_to(ROOT)).replace("\\", "/")

    # Skip pages that shouldn't have a byline
    skip_list = [
        "about/index.html",
        "how-it-works/index.html",
        "index.html",
        "404.html",
        "contact/index.html",
        "press/index.html",
        "privacy/index.html",
        "terms/index.html",
        "thank-you/index.html",
    ]
    if rel_str in skip_list:
        return None

    if 'By Emiliano · Last updated' in content:
        return None

    # Find the first H1
    match = H1_REGEX.search(content)
    if not match:
        return "no-h1"

    # Insert byline right after the H1
    indent = match.group(1)
    h1_block = match.group(2)
    replacement = f"{indent}{h1_block}\n{indent}{BYLINE}"

    content = content[:match.start()] + replacement + content[match.end():]

    path.write_text(content, encoding="utf-8")
    return "added byline"


def main():
    patched = []
    skipped = []
    errors = []

    for p in sorted(ROOT.rglob("*.html")):
        if ".git" in p.parts:
            continue
        result = patch(p)
        rel = p.relative_to(ROOT)
        if result is None:
            skipped.append(rel)
        elif isinstance(result, str) and result.startswith("error"):
            errors.append((rel, result))
        elif result == "no-h1":
            errors.append((rel, "no H1 found"))
        else:
            patched.append(rel)

    print(f"\n=== PATCHED {len(patched)} FILES ===")
    for f in patched:
        print(f"  ✓ {f}")

    print(f"\n=== SKIPPED {len(skipped)} FILES (already have byline or exempt) ===")

    if errors:
        print(f"\n=== ERRORS ({len(errors)}) ===")
        for f, e in errors:
            print(f"  ✗ {f}: {e}")


if __name__ == "__main__":
    main()
