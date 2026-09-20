#!/usr/bin/env python3
"""
Calccover — Patch broken calculator pages.
Fixes: 1) dangling JS from old submitLead, 2) missing .content-section wrappers + CSS.
"""
import os
import re

# Only process these slugs
TARGETS = {
    "workers-comp-insurance-calculator",
    "commercial-truck-insurance-calculator",
    "general-liability-insurance-calculator",
    "commercial-auto-insurance-calculator",
    "restaurant-insurance-calculator",
}

CONTENT_CSS = """
        .content-section{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:1.5rem;margin-bottom:2rem}
        .content-section h2{margin-top:0}
"""

def fix_js(html):
    """Remove dangling JS fragments left from submitLead removal."""
    # Pattern A: } else{alert(...)} inside another function's closing
    html = re.sub(
        r"\n\s*\}\s*\n\s*else\{alert\('Please enter a valid email address\.'\);\}\s*\n\s*\}",
        "\n        }",
        html
    )
    # Pattern B: bare alert + two closing braces
    html = re.sub(
        r"\n\s*alert\('Please enter a valid email address\.'\);\s*\n\s*\}\s*\n\s*\}",
        "\n}",
        html
    )
    # Pattern C: any remaining bare alert line
    html = re.sub(
        r"\n\s*alert\('Please enter a valid email address\.'\);",
        "",
        html
    )
    return html


def add_content_css(html):
    """Add .content-section CSS if not present."""
    if ".content-section" in html and "background:#fff;border:1px solid #e5e5e5" in html:
        return html
    # Insert before footer CSS rule
    marker = "        footer{"
    if marker in html:
        html = html.replace(marker, CONTENT_CSS + "\n" + marker, 1)
    return html


def wrap_content_sections(html):
    """Wrap the three content H2 sections in <section class='content-section'>."""
    if '<section class="content-section">' in html:
        return html  # already wrapped

    # Find start: first <h2> after the lead-form's closing </div>
    lead_end = html.find("</div>", html.find('<div class="lead-form"'))
    # Find the actual end of lead-form div: skip past the nested script
    lead_end = html.find("</div>", lead_end + 1)
    # Find the <h2>How Much or <h2>How to after that
    h2_match = re.search(r"(\s*<h2>(?:How Much|How to|What)", html[lead_end:])
    if not h2_match:
        print("  Could not find content start")
        return html
    content_start = lead_end + h2_match.start(1)

    # Find end: just before </div></main>
    end_match = html.find("</div></main>", content_start)
    if end_match == -1:
        print("  Could not find content end")
        return html

    content = html[content_start:end_match]

    # Split by <h2> boundaries and wrap each section
    parts = re.split(r"(?=\s*<h2>)", content)
    wrapped = ""
    for part in parts:
        if not part.strip():
            continue
        if part.strip().startswith("<h2>"):
            wrapped += '\n\n        <section class="content-section">' + part.rstrip() + "\n        </section>"
        else:
            wrapped += part

    html = html[:content_start] + wrapped + "\n\n    " + html[end_match:]
    return html


def patch_file(path, slug):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    original = html
    html = fix_js(html)
    html = add_content_css(html)
    html = wrap_content_sections(html)

    if html != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Patched: {path}")
        return True
    print(f"  No change: {path}")
    return False


def main():
    patched = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        slug = os.path.basename(root)
        if slug not in TARGETS:
            continue
        for file in files:
            if file == "index.html":
                path = os.path.join(root, file)
                if patch_file(path, slug):
                    patched += 1
    print(f"\nDone. Patched: {patched}")


if __name__ == "__main__":
    main()
