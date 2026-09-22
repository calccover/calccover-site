#!/usr/bin/env python3
"""Add og:image, Twitter Card tags, and favicon link to every page that's missing them."""
import os
import re

SKIP = {"scripts", ".github", "node_modules"}

OG_IMAGE_LINE = '<meta property="og:image" content="https://calccover.com/og-image.png">'
TWITTER_BLOCK = '''<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="https://calccover.com/og-image.png">'''
FAVICON_LINE = '<link rel="icon" href="/favicon.ico">'


def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    original = html

    # Extract title and description for the Twitter tags
    title_m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    desc_m = re.search(r'<meta name="description" content="(.*?)"', html)
    title = title_m.group(1).strip() if title_m else "Calccover"
    desc = desc_m.group(1).strip() if desc_m else "Free commercial insurance calculators."

    to_insert = []

    # Check each missing tag and only add what's needed
    if 'property="og:image"' not in html:
        to_insert.append(OG_IMAGE_LINE)

    if 'name="twitter:card"' not in html:
        twitter = TWITTER_BLOCK.replace("{TITLE}", title).replace("{DESC}", desc)
        to_insert.append(twitter)

    if 'rel="icon"' not in html:
        to_insert.append(FAVICON_LINE)

    if not to_insert:
        print(f"  ✓ Already complete: {path}")
        return False

    # Insert everything before </head>
    if "</head>" not in html:
        print(f"  ✗ No </head> tag: {path}")
        return False

    block = "\n".join(to_insert) + "\n"
    html = html.replace("</head>", block + "</head>", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Patched: {path} (added {len(to_insert)} tags)")
    return True


def main():
    patched = 0
    skipped = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for file in files:
            if file == "index.html":
                path = os.path.join(root, file)
                if patch(path):
                    patched += 1
                else:
                    skipped += 1
    print(f"\nDone. Patched: {patched}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
