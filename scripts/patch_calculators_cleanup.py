#!/usr/bin/env python3
"""
Cleanup pass:
- Remove byline from non-calculator pages (legal, contact, 404, etc.)
- Add missing byline to calculator pages
- Add missing footer to calculator pages
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BYLINE = '<p style="color:#777;font-size:.85rem;margin-bottom:.75rem">By Emiliano · Last updated 2026-09-27</p>'
BYLINE_REGEX = re.compile(r'\s*<p style="color:#777;font-size:.85rem;margin-bottom:.75rem">By Emiliano[^<]*</p>')

# Pages that should NOT have a byline
NO_BYLINE_PAGES = {
    "404.html",
    "contact/index.html",
    "press/index.html",
    "privacy/index.html",
    "terms/index.html",
    "thank-you/index.html",
    "about/index.html",
    "how-it-works/index.html",
    "index.html",
}

# Pages that SHOULD have a byline
CALCULATOR_PATTERN = re.compile(r'-calculator|commercial-insurance-costs-by-state')

FOOTER_NEW = '''<footer>
    <div class="container">
        <div>
            <a href="/">Home</a>
            <a href="/how-it-works/">How It Works</a>
            <a href="/about/">About</a>
            <a href="/contact/">Contact</a>
            <a href="/privacy/">Privacy</a>
            <a href="/terms/">Terms</a>
        </div>
        <div>© 2026 Calccover.</div>
    </div>
</footer>'''


def patch(path):
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"error: {e}"

    original = content
    changes = []
    rel_str = str(path.relative_to(ROOT)).replace("\\", "/")

    # 1. Remove byline from non-calculator pages
    if rel_str in NO_BYLINE_PAGES:
        if BYLINE_REGEX.search(content):
            content = BYLINE_REGEX.sub("", content)
            changes.append("removed byline (not a calculator page)")

    # 2. Calculator pages: ensure footer has How It Works + Home
    is_calculator = bool(CALCULATOR_PATTERN.search(rel_str))
    if is_calculator:
        footer_match = re.search(r'<footer>.*?</footer>', content, re.DOTALL)
        if footer_match:
            old_footer = footer_match.group(0)
            needs_home = '<a href="/">Home</a>' not in old_footer
            needs_how = '<a href="/how-it-works/">How It Works</a>' not in old_footer
            if needs_home or needs_how:
                content = content.replace(old_footer, FOOTER_NEW)
                changes.append("fixed footer")

        # 3. Calculator pages: ensure byline exists
        if 'By Emiliano · Last updated' not in content:
            h1_match = re.search(r'(<h1[^>]*>.*?</h1>)(\s*<p[^>]*>.*?</p>)', content, re.DOTALL)
            if h1_match:
                insertion = h1_match.group(0) + "\n        " + BYLINE
                content = content.replace(h1_match.group(0), insertion, 1)
                changes.append("added byline")
            else:
                changes.append("WARNING: no H1+p pattern for byline")

    if content != original:
        path.write_text(content, encoding="utf-8")
        return changes
    return None


def main():
    patched = []
    skipped = []

    for p in sorted(ROOT.rglob("*.html")):
        if ".git" in p.parts:
            continue
        result = patch(p)
        rel = p.relative_to(ROOT)
        if result is None:
            skipped.append(rel)
        elif isinstance(result, str) and result.startswith("error"):
            print(f"  ERROR {rel}: {result}")
        else:
            patched.append((rel, result))

    print(f"\n=== PATCHED {len(patched)} FILES ===")
    for f, changes in patched:
        print(f"  ✓ {f}")
        for c in changes:
            print(f"      - {c}")

    print(f"\n=== SKIPPED {len(skipped)} FILES (already correct) ===")


if __name__ == "__main__":
    main()
