#!/usr/bin/env python3
"""Shorten state page titles."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fix(content):
    match = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
    if not match:
        return content, False

    old = match.group(1).strip()
    if len(old) <= 60:
        return content, False

    # Extract state from any format
    m = re.match(r"^Commercial Insurance Cost in ([A-Za-z\s]+?)[\s:\u2014-]", old)
    if not m:
        return content, False

    state = m.group(1).strip()
    new = f"Commercial Insurance Cost in {state} (2026)"

    if len(new) > 60:
        return content, False

    content = content.replace(f"<title>{old}</title>", f"<title>{new}</title>", 1)
    # Also fix og:title and twitter:title
    for prefix in ['<meta property="og:title" content="',
                   '<meta name="twitter:title" content="']:
        content = content.replace(f'{prefix}{old}">', f'{prefix}{new}">')
    return content, True

fixed = 0
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in (".git", ".github", "scripts")]
    if "index.html" not in files:
        continue
    if "commercial-insurance-cost-in-" not in root:
        continue
    path = os.path.join(root, "index.html")
    with open(path, encoding="utf-8") as f:
        c = f.read()
    new_c, changed = fix(c)
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_c)
        print(f"  OK  {os.path.basename(root)}")
        fixed += 1

print(f"\nFixed {fixed} state titles")
