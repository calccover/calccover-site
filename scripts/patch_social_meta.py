#!/usr/bin/env python3
"""Add og:image, Twitter Card tags, and favicon link to every page."""
import os
import re

SKIP = {"scripts", ".github", "about", "contact", "privacy", "terms", "thank-you", "node_modules"}

META_BLOCK = '''<meta property="og:image" content="https://calccover.com/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="https://calccover.com/og-image.png">
<link rel="icon" href="/favicon.ico">
'''

def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    original = html

    if "og:image" in html:
        print(f"  Already has og:image: {path}")
        return False

    title_m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    desc_m = re.search(r'<meta name="description" content="(.*?)"', html)
    title = title_m.group(1).strip() if title_m else "Calccover"
    desc = desc_m.group(1).strip() if desc_m else ""

    block = META_BLOCK.replace("{TITLE}", title).replace("{DESC}", desc)

    if "</head>" in html:
        html = html.replace("</head>", block + "</head>", 1)
    else:
        print(f"  No </head>: {path}")
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Patched: {path}")
    return True

def main():
    patched = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for file in files:
            if file == "index.html":
                path = os.path.join(root, file)
                if patch(path):
                    patched += 1
    print(f"\nDone. Patched: {patched}")

if __name__ == "__main__":
    main()
