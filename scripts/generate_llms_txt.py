#!/usr/bin/env python3
"""Generate llms.txt for AI crawler discoverability."""
import os
import re
from xml.etree import ElementTree
import urllib.request

SITE = "https://calccover.com"
SITE_NAME = "Calccover"
SITE_DESC = "Free commercial insurance calculators for small business owners, contractors, and fleet operators."

# Fetch sitemap to get all pages
req = urllib.request.Request(f"{SITE}/sitemap.xml", headers={"User-Agent": "Mozilla/5.0"})
xml = urllib.request.urlopen(req).read().decode()
root = ElementTree.fromstring(xml)
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
urls = [loc.text for loc in root.findall(".//sm:loc", ns)]

# Group pages by type
calculators = [u for u in urls if "calculator" in u]
info_pages = [u for u in urls if any(x in u for x in ["/about/", "/contact/", "/privacy/", "/terms/"])]
research = [u for u in urls if "costs-by-state" in u or "study" in u]

lines = [
    f"# {SITE_NAME}",
    "",
    f"> {SITE_DESC}",
    "",
    "## Main Pages",
    f"- [Homepage]({SITE}/): Overview of all calculators",
]

if research:
    lines.append("")
    lines.append("## Research & Data")
    for url in research:
        lines.append(f"- [{url.split('/')[-2].replace('-', ' ').title()}]({url})")

if calculators:
    lines.append("")
    lines.append("## Free Calculators")
    for url in calculators[:20]:
        name = url.strip("/").split("/")[-1].replace("-", " ").title()
        lines.append(f"- [{name}]({url})")

if info_pages:
    lines.append("")
    lines.append("## Information")
    for url in info_pages:
        name = url.strip("/").split("/")[-1].title()
        lines.append(f"- [{name}]({url})")

lines.append("")
lines.append(f"## Contact")
lines.append(f"- Email: hello@calccover.com")

output = "\n".join(lines)

with open("llms.txt", "w") as f:
    f.write(output)

print(f"Wrote llms.txt ({len(output)} bytes)")
print(output[:500])
