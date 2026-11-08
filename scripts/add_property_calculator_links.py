"""
Add / upgrade internal links to /commercial-property-insurance-calculator/
across the homepage and all 50 commercial-insurance-cost-in-[state] pages.

Idempotent: safe to re-run. If a page is already updated, it is skipped.

Changes made:
  - State pages: 2 edits each
    1. Insert contextual exact-match link in "Top industries" paragraph
    2. Upgrade grid anchor "Commercial Property Calculator" -> "Commercial Property Insurance Calculator"
  - Homepage: 1 edit
    1. Upgrade card H3 "Commercial Property Calculator" -> "Commercial Property Insurance Calculator"
"""

from pathlib import Path

REPO_ROOT = Path(".")
TARGET = "/commercial-property-insurance-calculator/"

STATES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new-hampshire", "new-jersey", "new-mexico", "new-york",
    "north-carolina", "north-dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode-island", "south-carolina", "south-dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west-virginia", "wisconsin", "wyoming",
]

STATE_NAMES = {slug: slug.replace("-", " ").title() for slug in STATES}

# Old pattern to find
OLD_P = (
    "<p>If your business is in one of these industries, "
    "use our free calculators to get a specific estimate:</p>"
)

# Old grid link
OLD_GRID_LINK = f'<a href="{TARGET}">Commercial Property Calculator →</a>'
NEW_GRID_LINK = f'<a href="{TARGET}">Commercial Property Insurance Calculator →</a>'

# Homepage old / new
OLD_H3 = "<h3>Commercial Property Calculator</h3>"
NEW_H3 = "<h3>Commercial Property Insurance Calculator</h3>"


def process_state_page(slug: str, html: str):
    state_name = STATE_NAMES[slug]
    changes = []

    # Change 1: contextual in-body link with exact-match anchor
    new_p = (
        f'<p>If your business is in one of these industries, use our free '
        f'<a href="{TARGET}">commercial property insurance calculator</a> '
        f'or any of the other tools below to get a specific estimate for your '
        f'{state_name} business:</p>'
    )
    if OLD_P in html:
        html = html.replace(OLD_P, new_p, 1)
        changes.append("added contextual link")

    # Change 2: upgrade grid anchor (add "Insurance")
    if OLD_GRID_LINK in html:
        html = html.replace(OLD_GRID_LINK, NEW_GRID_LINK, 1)
        changes.append("upgraded grid anchor")

    return html, changes


def process_homepage(html: str):
    changes = []
    if OLD_H3 in html:
        html = html.replace(OLD_H3, NEW_H3, 1)
        changes.append("upgraded card H3")
    return html, changes


def main():
    files_changed = 0
    files_skipped = 0
    errors = []

    # 1. Homepage
    hp = REPO_ROOT / "index.html"
    if not hp.exists():
        errors.append("index.html not found at repo root")
    else:
        html = hp.read_text(encoding="utf-8")
        new_html, changes = process_homepage(html)
        if changes:
            hp.write_text(new_html, encoding="utf-8")
            print(f"✓ index.html — {', '.join(changes)}")
            files_changed += 1
        else:
            print(f"○ index.html — already up to date, skipped")
            files_skipped += 1

    # 2. State pages
    for slug in STATES:
        path = REPO_ROOT / f"commercial-insurance-cost-in-{slug}" / "index.html"
        if not path.exists():
            errors.append(f"missing file: {path}")
            print(f"✗ {slug} — file not found")
            continue

        html = path.read_text(encoding="utf-8")
        new_html, changes = process_state_page(slug, html)

        if new_html != html:
            path.write_text(new_html, encoding="utf-8")
            print(f"✓ {slug} — {', '.join(changes)}")
            files_changed += 1
        else:
            print(f"○ {slug} — already up to date, skipped")
            files_skipped += 1

    # 3. Summary
    print("")
    print("=" * 60)
    print(f"Files changed:  {files_changed}")
    print(f"Files skipped:  {files_skipped}")
    print(f"Errors:         {len(errors)}")
    if errors:
        print("")
        print("Errors:")
        for e in errors:
            print(f"  - {e}")


if __name__ == "__main__":
    main()
