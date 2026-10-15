#!/usr/bin/env python3
"""
Fix the two high-value SEO issues from the audit:
1. Shorten long titles on state pages (>60 chars)
2. Fix H1 -> H3 heading jumps on calculator pages
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fix_state_page_title(content):
    """
    State page titles look like:
    'Commercial Insurance Cost in Alabama: 2026 Rates & Benchmarks — Calccover'
    Shorten to: 'Commercial Insurance Cost in Alabama (2026)'
    """
    match = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
    if not match:
        return content, False

    old_title = match.group(1).strip()
    if len(old_title) <= 60:
        return content, False

    # Extract state name from "Commercial Insurance Cost in X:"
    m = re.match(r"^Commercial Insurance Cost in ([^:]+):", old_title)
    if m:
        state = m.group(1).strip()
        new_title = f"Commercial Insurance Cost in {state} (2026)"
        if len(new_title) <= 60:
            content = content.replace(f"<title>{old_title}</title>", f"<title>{new_title}</title>", 1)
            # Also fix og:title and twitter:title
            content = content.replace(f'<meta property="og:title" content="{old_title}">',
                                      f'<meta property="og:title" content="{new_title}">')
            content = content.replace(f'<meta name="twitter:title" content="{old_title}">',
                                      f'<meta name="twitter:title" content="{new_title}">')
            return content, True

    return content, False


def fix_heading_jump(content):
    """
    Fix H1 -> H3 heading jumps.
    Strategy: convert the FIRST H3 after the H1 to an H2.
    This preserves content while fixing the semantic jump.
    """
    # Find first H3 in the document
    h1_match = re.search(r"<h1[^>]*>.*?</h1>", content, re.DOTALL)
    if not h1_match:
        return content, False

    after_h1 = content[h1_match.end():]

    # Look for the first heading tag after H1
    next_heading = re.search(r"<h([1-6])[^>]*>", after_h1)
    if not next_heading:
        return content, False

    heading_level = int(next_heading.group(1))

    # If the next heading is H3, convert it to H2
    if heading_level == 3:
        # Find the full H3 block
        h3_start = h1_match.end() + next_heading.start()
        h3_end_match = re.search(r"</h3>", content[h3_start:])
        if h3_end_match:
            h3_end = h3_start + h3_end_match.end()
            old_h3_block = content[h3_start:h3_end]
            new_h2_block = old_h3_block.replace("<h3", "<h2", 1).replace("</h3>", "</h2>", 1)
            content = content[:h3_start] + new_h2_block + content[h3_end:]
            return content, True

    return content, False


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    title_fixed = False
    heading_fixed = False

    # Fix 1: state page title
    if "/commercial-insurance-cost-in-" in filepath:
        content, title_fixed = fix_state_page_title(content)

    # Fix 2: heading jump (any calculator or best-of page)
    if ("calculator" in filepath or "/best/" in filepath):
        content, heading_fixed = fix_heading_jump(content)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return title_fixed, heading_fixed

    return False, False


def main():
    title_count = 0
    heading_count = 0
    total = 0

    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".github", "scripts", ".next", "dist", "out")]
        if "index.html" not in files:
            continue

        filepath = os.path.join(root, "index.html")
        rel = os.path.relpath(filepath, ROOT).replace("\\", "/")

        t_fixed, h_fixed = process_file(filepath)
        if t_fixed or h_fixed:
            parts = []
            if t_fixed:
                parts.append("title")
                title_count += 1
            if h_fixed:
                parts.append("heading")
                heading_count += 1
            print(f"  OK  {rel}  [{', '.join(parts)}]")
            total += 1

    print(f"\nFixed {total} pages")
    print(f"  Titles shortened: {title_count}")
    print(f"  Heading jumps fixed: {heading_count}")


if __name__ == "__main__":
    main()
