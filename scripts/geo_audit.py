#!/usr/bin/env python3
"""
GEO audit for Calccover.com — audits EVERY page in the sitemap.

Checks AI crawler access, llms.txt, schema markup, and citability.
Writes a detailed report to geo_report.md.

Usage:
    python scripts/geo_audit.py
"""
import os
import re
import json
import urllib.request
import time
from xml.etree import ElementTree

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup

SITE_URL = os.environ.get("SITE_URL", "https://calccover.com")
SITEMAP_URL = f"{SITE_URL}/sitemap.xml"
REPORT_FILE = "geo_report.md"
JSON_FILE = "geo_report.json"

AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "ClaudeBot", "Claude-Web",
    "PerplexityBot", "Google-Extended", "anthropic-ai",
    "CCBot", "Bytespider", "Amazonbot",
]

UA = "Mozilla/5.0 (compatible; GEOAuditBot/1.0)"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def get_sitemap_urls():
    try:
        status, xml = fetch(SITEMAP_URL)
        root = ElementTree.fromstring(xml)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        return [loc.text for loc in root.findall(".//sm:loc", ns)]
    except Exception as e:
        print(f"Sitemap failed: {e}")
        return []


def check_robots():
    print("\n=== AI CRAWLER ACCESS ===")
    try:
        status, robots = fetch(f"{SITE_URL}/robots.txt")
    except Exception as e:
        return {"error": str(e), "blocked": []}

    blocked = []
    for crawler in AI_CRAWLERS:
        pattern = rf"User-agent:\s*{crawler}\s*\n(.*?)(?=\nUser-agent|\Z)"
        match = re.search(pattern, robots, re.IGNORECASE | re.DOTALL)
        if match and "Disallow: /" in match.group(1):
            blocked.append(crawler)
            print(f"  BLOCKED: {crawler}")
        else:
            print(f"  Allowed: {crawler}")

    return {"blocked": blocked}


def check_llms_txt():
    print("\n=== LLMS.TXT ===")
    try:
        status, content = fetch(f"{SITE_URL}/llms.txt")
        if status == 200:
            lines = content.split("\n")
            has_title = any(l.startswith("# ") for l in lines)
            has_description = any(l.startswith("> ") for l in lines)
            has_sections = any(l.startswith("## ") for l in lines)
            print(f"  Found ({len(lines)} lines)")
            print(f"  Title: {has_title}")
            print(f"  Description: {has_description}")
            print(f"  Sections: {has_sections}")
            return {"found": True, "lines": len(lines), "title": has_title,
                    "desc": has_description, "sections": has_sections}
    except Exception:
        pass
    print("  Missing")
    return {"found": False}


def check_schema(soup):
    schemas = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if "@graph" in data:
                    for node in data["@graph"]:
                        schemas.append(node.get("@type", "Unknown"))
                else:
                    schemas.append(data.get("@type", "Unknown"))
        except Exception:
            pass
    return schemas


def check_citability(soup):
    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return {"score": 0, "notes": ["No main content"]}

    notes = []
    score = 100

    # Long paragraphs
    paragraphs = main.find_all("p")
    long_p = [p for p in paragraphs if len(p.get_text().split()) > 150]
    if long_p:
        notes.append(f"{len(long_p)} paragraphs over 150 words")
        score -= min(20, len(long_p) * 5)

    # Statistics
    text = main.get_text()
    stats = len(re.findall(r"\$[\d,]+|\d+%|\d+\.\d+|\d+ (?:billion|million|thousand)", text))
    if stats < 5:
        notes.append(f"Only {stats} statistics found (aim for 10+)")
        score -= 10
    else:
        notes.append(f"{stats} statistics found")

    # Lists
    lists = main.find_all(["ul", "ol"])
    if len(lists) < 2:
        notes.append(f"Only {len(lists)} lists (aim for 3+)")
        score -= 5
    else:
        notes.append(f"{len(lists)} lists found")

    # Tables
    tables = main.find_all("table")
    if len(tables) >= 1:
        notes.append(f"{len(tables)} data table(s) found")

    # Question headings
    headings = main.find_all(["h2", "h3"])
    q_headings = [
        h for h in headings
        if "?" in h.get_text() or h.get_text().strip().lower().startswith(
            ("how", "what", "why", "when", "where")
        )
    ]
    if q_headings:
        notes.append(f"{len(q_headings)} question-based headings")

    return {"score": max(0, score), "notes": notes}


def audit_page(url):
    try:
        status, html = fetch(url)
    except Exception as e:
        return {"url": url, "error": str(e)}

    soup = BeautifulSoup(html, "html.parser")
    schemas = check_schema(soup)
    citability = check_citability(soup)

    return {
        "url": url,
        "schemas": schemas,
        "citability_score": citability["score"],
        "citability_notes": citability["notes"],
        "word_count": len(soup.get_text().split()),
    }


def main():
    print(f"\n{'#' * 60}")
    print(f"# FULL GEO AUDIT: {SITE_URL}")
    print(f"# {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#' * 60}")

    robots = check_robots()
    llms = check_llms_txt()

    urls = get_sitemap_urls()
    print(f"\n\nFound {len(urls)} pages in sitemap")
    print(f"Auditing ALL {len(urls)} pages (this takes 5-10 minutes)\n")

    results = []
    total_citability = 0
    low_scorers = []

    for i, url in enumerate(urls, 1):
        short = url.replace(SITE_URL, "")[:70]
        print(f"[{i:>3}/{len(urls)}] {short}")

        result = audit_page(url)
        results.append(result)

        if "citability_score" in result:
            total_citability += result["citability_score"]
            if result["citability_score"] < 95:
                low_scorers.append((url, result["citability_score"]))
        time.sleep(0.3)

    avg = total_citability / len(results) if results else 0

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"AI crawlers blocked: {len(robots.get('blocked', []))}")
    print(f"llms.txt present: {llms.get('found', False)}")
    print(f"Pages audited: {len(results)}")
    print(f"Average citability: {avg:.1f}/100")
    print(f"Pages below 95: {len(low_scorers)}")

    if low_scorers:
        print(f"\nPages needing improvement:")
        for url, score in low_scorers:
            print(f"  {score}/100  {url}")

    # Write markdown report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# GEO Audit Report — {SITE_URL}\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Pages audited:** {len(results)}\n\n")
        f.write(f"**Average citability:** {avg:.1f}/100\n\n")
        f.write(f"**AI crawlers blocked:** {len(robots.get('blocked', []))}\n\n")
        f.write(f"**llms.txt present:** {llms.get('found', False)}\n\n")
        f.write(f"---\n\n")
        f.write(f"## Pages scoring below 95\n\n")
        if low_scorers:
            f.write("| URL | Score | Issues |\n|---|---|---|\n")
            for url, score in low_scorers:
                r = next((r for r in results if r.get("url") == url), {})
                notes = ", ".join(r.get("citability_notes", []))
                f.write(f"| {url} | {score} | {notes} |\n")
        else:
            f.write("None — all pages score 95 or higher.\n")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"site": SITE_URL, "avg_citability": avg,
                   "pages_audited": len(results), "results": results}, f, indent=2)

    print(f"\nReport saved to {REPORT_FILE}")
    print(f"Raw data saved to {JSON_FILE}")


if __name__ == "__main__":
    main()
