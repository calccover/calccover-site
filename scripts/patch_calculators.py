#!/usr/bin/env python3
"""
Patch all calccover calculator pages:
- Add "How It Works" to nav
- Add "How It Works" + "Home" to footer
- Add author byline under the H1
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BYLINE = '<p style="color:#777;font-size:.85rem;margin-bottom:.75rem">By Emiliano · Last updated 2026-09-27</p>'

# Nav patterns — handle inline and multiline
NAV_OLD_PATTERNS = [
    re.compile(r'<nav>\s*<a href="/about/">About</a>\s*<a href="/contact/">Contact</a>\s*</nav>'),
]
NAV_NEW = '<nav><a href="/how-it-works/">How It Works</a><a href="/about/">About</a><a href="/contact/">Contact</a></nav>'

# Footer patterns
FOOTER_OLD_PATTERNS = [
    re.compile(
        r'<footer>\s*<div class="container">\s*<div>\s*<a href="/about/">About</a>\s*<a href="/contact/">Contact</a>\s*<a href="/privacy/">Privacy</a>\s*<a href="/terms/">Terms</a>\s*</div>\s*<div>© 2026 Calccover\.</div>\s*</div>\s*</footer>',
        re.DOTALL
    ),
    re.compile(
        r'<footer><div class="container"><div><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div><div>© 2026 Calccover\.</div></div></footer>'
    ),
]
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


def patch_file(path):
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"error: {e}"

    original = content
    changes = []

    # 1. Nav — insert "How It Works" if not present
    if 'href="/how-it-works/"' not in content:
        # Try structured patterns first
        replaced = False
        for pattern in NAV_OLD_PATTERNS:
            if pattern.search(content):
                content = pattern.sub(NAV_NEW, content)
                changes.append("added How It Works to nav")
                replaced = True
                break

        # Fallback: generic nav insertion
        if not replaced:
            nav_match = re.search(r'<nav[^>]*>(.*?)</nav>', content, re.DOTALL)
            if nav_match and '/how-it-works/' not in nav_match.group(1):
                content = re.sub(
                    r'(<nav[^>]*>)',
                    r'\1<a href="/how-it-works/">How It Works</a>',
                    content,
                    count=1
                )
                changes.append("added How It Works to nav (generic)")

    # 2. Footer — replace with new version
    footer_replaced = False
    for pattern in FOOTER_OLD_PATTERNS:
        if pattern.search(content):
            content = pattern.sub(FOOTER_NEW, content)
            changes.append("updated footer")
            footer_replaced = True
            break

    # Fallback: generic footer link injection
    if not footer_replaced and 'href="/how-it-works/"' not in content:
        # Find footer block
        footer_match = re.search(r'<footer>.*?</footer>', content, re.DOTALL)
        if footer_match:
            old_footer = footer_match.group(0)
            new_footer = old_footer
            # Add Home link if missing
            if '<a href="/">Home</a>' not in new_footer:
                new_footer = new_footer.replace(
                    '<a href="/about/">About</a>',
                    '<a href="/">Home</a>\n            <a href="/how-it-works/">How It Works</a>\n            <a href="/about/">About</a>',
                    1
                )
            content = content.replace(old_footer, new_footer)
            changes.append("updated footer (generic)")

    # 3. Byline — add if not already present
    if 'By Emiliano · Last updated' not in content:
        # Find the first <p> after the first <h1> (the subhead)
        h1_match = re.search(r'(<h1[^>]*>.*?</h1>)(\s*<p[^>]*>.*?</p>)', content, re.DOTALL)
        if h1_match:
            insertion = h1_match.group(0) + "\n        " + BYLINE
            content = content.replace(h1_match.group(0), insertion, 1)
            changes.append("added author byline")

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
        # Skip pages we already wrote manually
        if p.name == "index.html" and p.parent == ROOT:
            skipped.append(p.relative_to(ROOT))
            continue
        if "how-it-works" in str(p) or "about" in str(p):
            skipped.append(p.relative_to(ROOT))
            continue

        result = patch_file(p)
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

    print(f"\n=== SKIPPED {len(skipped)} FILES ===")
    for f in skipped:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
