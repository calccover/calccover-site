"""Add E&O calculator links to all 50 commercial-insurance-cost-in-[state] pages."""
from pathlib import Path

TARGET = "/errors-omissions-insurance-calculator/"

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

STATE_NAMES = {s: s.replace("-", " ").title() for s in STATES}

# Anchor rotation — exact match used ~5 times, variations for the rest
ANCHORS = [
    "errors and omissions insurance calculator",
    "errors and omissions insurance calculator",
    "errors and omissions insurance calculator",
    "errors and omissions insurance calculator",
    "errors and omissions insurance calculator",
    "E&O insurance calculator",
    "E&O calculator",
    "errors and omissions calculator",
    "calculate your E&O premium",
    "estimate your E&O insurance cost",
    "errors and omissions insurance estimate",
    "E&O premium calculator",
]

changed = 0
skipped = 0
errors = []

for i, slug in enumerate(STATES):
    path = Path(f"commercial-insurance-cost-in-{slug}") / "index.html"
    state_name = STATE_NAMES[slug]

    if not path.exists():
        print(f"ERROR {slug}: file not found")
        errors.append(slug)
        continue

    html = path.read_text(encoding="utf-8")

    if TARGET in html:
        print(f"SKIP {slug}: already linked")
        skipped += 1
        continue

    anchor = ANCHORS[i % len(ANCHORS)]

    # Insert contextual paragraph before the calc-links grid
    old_block = '<div class="calc-links">'
    new_block = (
        f'<p>Professional service businesses and consultants in {state_name} '
        f'should also consider errors and omissions coverage. Use our '
        f'<a href="{TARGET}">{anchor}</a> to estimate your specific E&amp;O premium.</p>\n'
        f'<div class="calc-links">'
    )

    if old_block not in html:
        print(f"ERROR {slug}: calc-links div not found")
        errors.append(slug)
        continue

    html = html.replace(old_block, new_block, 1)

    # Add grid link to E&O calculator after Workers' Comp link
    grid_line = '<a href="/workers-comp-insurance-calculator/">Workers\' Comp Calculator &rarr;</a>'
    if grid_line not in html:
        grid_line = '<a href="/workers-comp-insurance-calculator/">Workers\' Comp Calculator →</a>'
    new_grid_line = grid_line + '\n<a href="/errors-omissions-insurance-calculator/">E&O Calculator →</a>'

    if grid_line in html:
        html = html.replace(grid_line, new_grid_line, 1)

    path.write_text(html, encoding="utf-8")
    print(f"OK   {slug}: contextual + grid link added")
    changed += 1

print("=" * 50)
print(f"Changed: {changed}  |  Skipped: {skipped}  |  Errors: {len(errors)}")