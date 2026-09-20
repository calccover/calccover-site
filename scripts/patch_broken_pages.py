#!/usr/bin/env python3
"""
Calccover — Fix broken calculator pages.
Simple string-based patching. No complex regex.
"""
import os

TARGETS = [
    "workers-comp-insurance-calculator",
    "commercial-truck-insurance-calculator",
    "general-liability-insurance-calculator",
    "commercial-auto-insurance-calculator",
    "restaurant-insurance-calculator",
]

CONTENT_CSS = "        .content-section{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:1.5rem;margin-bottom:2rem}\n        .content-section h2{margin-top:0}\n"

def fix_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"  Could not read {path}: {e}")
        return False

    original = html

    # Fix 1: Remove dangling alert fragments
    html = html.replace("else{alert('Please enter a valid email address.');}", "")
    html = html.replace("alert('Please enter a valid email address.');", "")
    html = html.replace("alert('Thanks! A broker will contact you at '+email+' shortly.');", "")

    # Fix 2: Add content-section CSS
    if ".content-section{" not in html:
        if "        footer{" in html:
            html = html.replace("        footer{", CONTENT_CSS + "        footer{", 1)
            print(f"  Added content-section CSS")

    # Fix 3: Wrap content sections in <section class="content-section">
    # Find first content heading
    markers = ["<h2>How Much", "<h2>How to", "<h2>What Factors", "<h2>How Does"]
    content_start = -1
    for m in markers:
        idx = html.find(m)
        if idx != -1:
            content_start = idx
            break

    if content_start == -1:
        print(f"  No content heading found")
    elif '<section class="content-section">' in html:
        print(f"  Content already wrapped")
    else:
        # Find the end of content (before footer or before </main>)
        ends = ["</div></main>", "<footer", "</main>"]
        content_end = -1
        for e in ends:
            idx = html.find(e, content_start)
            if idx != -1:
                if content_end == -1 or idx < content_end:
                    content_end = idx

        if content_end == -1:
            print(f"  No content end found")
        else:
            content = html[content_start:content_end]
            # Split by <h2> and wrap each in section
            parts = content.split("<h2>")
            wrapped = parts[0]  # leading whitespace
            for part in parts[1:]:
                if part.strip():
                    wrapped += '\n\n        <section class="content-section">\n        <h2>' + part.rstrip() + '\n        </section>'
            html = html[:content_start] + wrapped + "\n\n    " + html[content_end:]
            print(f"  Wrapped content sections")

    if html != original:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  ✅ Patched")
            return True
        except Exception as e:
            print(f"  Could not write {path}: {e}")
            return False
    else:
        print(f"  ⚠️  No changes")
        return False


def main():
    print("Starting patch...")
    patched = 0
    for slug in TARGETS:
        path = os.path.join(".", slug, "index.html")
        print(f"\nProcessing: {path}")
        if not os.path.exists(path):
            print(f"  File does not exist")
            continue
        if fix_file(path):
            patched += 1
    print(f"\nDone. Patched: {patched}/{len(TARGETS)}")


if __name__ == "__main__":
    main()
