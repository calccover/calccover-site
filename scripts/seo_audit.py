#!/usr/bin/env python3
"""
On-page SEO audit for static sites.
Crawls sitemap.xml, checks every page, scores 0-100, reports issues.
"""
import os
import sys
import re
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from xml.etree import ElementTree

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing beautifulsoup4...")
    os.system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup

SITE_URL = os.environ.get("SITE_URL", "https://calccover.com")
SITEMAP_URL = f"{SITE_URL}/sitemap.xml"
REPORT_FILE = "seo_report.json"

UA = "Mozilla/5.0 (compatible; SEOAuditBot/1.0)"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def get_sitemap_urls():
    try:
        status, xml = fetch(SITEMAP_URL)
        if status != 200:
            print(f"Sitemap returned {status}")
            return []
        root = ElementTree.fromstring(xml)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        return [loc.text for loc in root.findall(".//sm:loc", ns)]
    except Exception as e:
        print(f"Sitemap fetch failed: {e}")
        return []


def audit_page(url):
    issues = []
    warnings = []
    score = 100

    try:
        status, html = fetch(url)
    except Exception as e:
        return {"url": url, "score": 0, "issues": [f"Fetch failed: {e}"], "warnings": []}

    if status != 200:
        return {"url": url, "score": 0, "issues": [f"HTTP {status}"], "warnings": []}

    soup = BeautifulSoup(html, "html.parser")

    # 1. Title tag
    title = soup.find("title")
    if not title or not title.text.strip():
        issues.append("Missing or empty <title>")
        score -= 15
    elif len(title.text) > 60:
        warnings.append(f"Title too long ({len(title.text)} chars, max 60)")
        score -= 3
    elif len(title.text) < 30:
        warnings.append(f"Title too short ({len(title.text)} chars, min 30)")
        score -= 2

    # 2. Meta description
    desc = soup.find("meta", attrs={"name": "description"})
    if not desc or not desc.get("content", "").strip():
        issues.append("Missing meta description")
        score -= 15
    elif len(desc["content"]) > 160:
        warnings.append(f"Meta description too long ({len(desc['content'])} chars)")
        score -= 3
    elif len(desc["content"]) < 70:
        warnings.append(f"Meta description too short ({len(desc['content'])} chars)")
        score -= 2

    # 3. H1 tag
    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        issues.append("Missing H1")
        score -= 15
    elif len(h1s) > 1:
        warnings.append(f"Multiple H1 tags ({len(h1s)})")
        score -= 5

    # 4. Canonical
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if not canonical:
        issues.append("Missing canonical tag")
        score -= 10
    elif canonical.get("href") != url and canonical.get("href") != url.rstrip("/"):
        warnings.append(f"Canonical mismatch: {canonical.get('href')} vs {url}")
        score -= 3

    # 5. Open Graph
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_url = soup.find("meta", attrs={"property": "og:url"})
    missing_og = [x for x, y in [("og:title", og_title), ("og:description", og_desc), ("og:url", og_url)] if not y]
    if missing_og:
        warnings.append(f"Missing Open Graph tags: {', '.join(missing_og)}")
        score -= 5

    # 6. Robots meta (accidental noindex)
    robots = soup.find("meta", attrs={"name": "robots"})
    if robots and "noindex" in robots.get("content", "").lower():
        issues.append("CRITICAL: Page has noindex directive")
        score -= 50

    # 7. JSON-LD structured data
    jsonld = soup.find_all("script", attrs={"type": "application/ld+json"})
    if not jsonld:
        warnings.append("No JSON-LD structured data")
        score -= 5

    # 8. Image alt text
    images = soup.find_all("img")
    if images:
        missing_alt = [img for img in images if not img.get("alt")]
        if missing_alt:
            pct = len(missing_alt) / len(images) * 100
            warnings.append(f"{len(missing_alt)}/{len(images)} images missing alt text")
            score -= min(10, int(pct / 10))

    # 9. Heading hierarchy
    headings = soup.find_all(re.compile("^h[1-6]$"))
    levels = [int(h.name[1]) for h in headings]
    for i in range(1, len(levels)):
        if levels[i] - levels[i-1] > 1:
            warnings.append(f"Heading jump: {levels[i-1]} to {levels[i]}")
            score -= 2
            break

    # 10. Internal links
    links = soup.find_all("a", href=True)
    internal = [l for l in links if l["href"].startswith("/") or SITE_URL in l["href"]]
    if len(internal) < 3:
        warnings.append(f"Few internal links ({len(internal)})")
        score -= 3

    # 11. Viewport meta
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        issues.append("Missing viewport meta tag")
        score -= 10

    # 12. Language attribute
    html_tag = soup.find("html")
    if not html_tag or not html_tag.get("lang"):
        warnings.append("Missing lang attribute on <html>")
        score -= 3

    # 13. Word count
    text = soup.get_text()
    words = len(text.split())
    if words < 200:
        warnings.append(f"Thin content ({words} words)")
        score -= 5

    # 14. HTTPS
    if not url.startswith("https://"):
        issues.append("Not served over HTTPS")
        score -= 20

    # 15. Sitemap presence (checked at page level via sitemap crawl)

    return {
        "url": url,
        "score": max(0, score),
        "issues": issues,
        "warnings": warnings,
        "word_count": words if 'words' in dir() else 0,
    }


def main():
    print(f"Auditing {SITE_URL}")
    urls = get_sitemap_urls()
    if not urls:
        print("No URLs found in sitemap. Aborting.")
        sys.exit(1)

    print(f"Found {len(urls)} URLs in sitemap\n")
    results = []
    total_score = 0
    critical_count = 0

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        result = audit_page(url)
        results.append(result)
        total_score += result["score"]
        if result["issues"]:
            critical_count += len(result["issues"])
            for issue in result["issues"]:
                print(f"  ❌ {issue}")
        for warning in result["warnings"]:
            print(f"  ⚠️  {warning}")
        print(f"  Score: {result['score']}/100\n")
        time.sleep(0.5)

    avg_score = total_score / len(results) if results else 0

    report = {
        "site": SITE_URL,
        "audited_at": datetime.utcnow().isoformat() + "Z",
        "pages_audited": len(results),
        "average_score": round(avg_score, 1),
        "critical_issues": critical_count,
        "results": results,
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=" * 60)
    print(f"SUMMARY: {len(results)} pages | Avg score: {avg_score:.1f}/100 | Critical issues: {critical_count}")
    print(f"Report saved to {REPORT_FILE}")

    if critical_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
