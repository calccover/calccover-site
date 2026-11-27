"""Add cost guide links to 8 industry hub pages."""
from pathlib import Path

HUBS = [
    ("restaurant-insurance", "Property damage from fire, water, or equipment failure is the biggest single risk for a restaurant."),
    ("retail-insurance", "Property and inventory are the two biggest exposure categories for retail."),
    ("real-estate-insurance", "Property insurance is the core coverage for any real estate business."),
    ("healthcare-practice-insurance", "Medical office buildings carry property exposure beyond tenant improvements."),
    ("beauty-and-wellness-insurance", "Salon and spa buildouts are often the largest insurable asset for beauty businesses."),
    ("nonprofit-insurance", "Nonprofits that own their facility need commercial property coverage."),
    ("professional-services-insurance", "Office buildout and equipment are your primary property exposure."),
    ("trucking-insurance", "Terminals and warehouses are covered under commercial property, not just commercial auto."),
]

LINK = "/commercial-property-insurance-cost/"
MARKER = '<h2>Related guides and resources</h2>'

changed = 0
skipped = 0
errors = []

for slug, intro in HUBS:
    path = Path(slug) / "index.html"
    if not path.exists():
        print(f"❌ {slug}: FILE NOT FOUND at {path}")
        errors.append(slug)
        continue

    html = path.read_text(encoding="utf-8")

    if LINK in html:
        print(f"○ {slug}: already linked, skipped")
        skipped += 1
        continue

    if MARKER not in html:
        print(f"❌ {slug}: no 'Related guides' section — manual edit needed")
        errors.append(slug)
        continue

    para = (
        f'<p>{intro} See our '
        f'<a href="{LINK}">commercial property insurance cost guide</a> '
        f'for average premiums by state and construction type.</p>\n'
    )

    html = html.replace(MARKER, para + MARKER, 1)
    path.write_text(html, encoding="utf-8")
    print(f"✓ {slug}: link added")
    changed += 1

print("=" * 50)
print(f"Changed: {changed}  |  Skipped: {skipped}  |  Errors: {len(errors)}")