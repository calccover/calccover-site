"""
Add /commercial-property-insurance-cost/ links to all 50 state pages.
Inserts a contextual link in the "What commercial insurance costs in [State]"
section, right after the first paragraph.
"""

from pathlib import Path

REPO_ROOT = Path(".")
TARGET = "/commercial-property-insurance-cost/"

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

# Insert before the "Here's the 2026 cost breakdown" paragraph
ANCHOR_TEXT = "<p>Here's the 2026 cost breakdown by coverage type for {state}:</p>"

NEW_PARAGRAPH_TEMPLATE = (
    '<p>For a full cost breakdown covering property insurance specifically, '
    'see our <a href="{target}">commercial property insurance cost guide</a> — '
    'state averages, construction type rates, and occupancy benchmarks.</p>\n'
)


def process_state_page(slug: str, html: str):
    state_name = STATE_NAMES[slug]
    if TARGET in html:
        return html, []  # already linked

    changes = []
    find_text = ANCHOR_TEXT.format(state=state_name)
    if find_text in html:
        insert_text = (
            NEW_PARAGRAPH_TEMPLATE.format(target=TARGET) + find_text
        )
        html = html.replace(find_text, insert_text, 1)
        changes.append("added cost guide link")

    return html, changes


def main():
    files_changed = 0
    files_skipped = 0
    errors = []

    for slug in STATES:
        path = REPO_ROOT / f"commercial-insurance-cost-in-{slug}" / "index.html"
        if not path.exists():
            errors.append(f"missing file: {path}")
            continue

        html = path.read_text(encoding="utf-8")
        new_html, changes = process_state_page(slug, html)

        if new_html != html:
            path.write_text(new_html, encoding="utf-8")
            print(f"✓ {slug} — {', '.join(changes)}")
            files_changed += 1
        else:
            print(f"○ {slug} — skipped (already linked or pattern not found)")
            files_skipped += 1

    print("=" * 60)
    print(f"Files changed: {files_changed}  |  Skipped: {files_skipped}  |  Errors: {len(errors)}")


if __name__ == "__main__":
    main()