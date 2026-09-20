#!/usr/bin/env python3
"""
Calccover — Replace FormSubmit forms with Web3Forms across all calculator pages.
"""
import os
import re

# YOUR ACCESS KEY — replace this with your real key
ACCESS_KEY = "7ddf27ee-45e4-4fe4-afd3-5b802ece6846"

SKIP = {"scripts", ".github", "about", "contact", "privacy", "terms", "thank-you", "node_modules"}

FORM_TEMPLATE = '''<form action="https://api.web3forms.com/submit" method="POST">
    <input type="hidden" name="access_key" value="{ACCESS_KEY}">
    <input type="email" name="email" required placeholder="your@email.com">
    <input type="hidden" name="calculator" value="{NAME}">
    <input type="hidden" name="page_url" id="pageUrl" value="">
    <input type="hidden" name="subject" value="New quote request — {NAME}">
    <input type="hidden" name="redirect" value="https://calccover.com/thank-you/">
    <button type="submit">Get a Free Quote</button>
</form>
<script>document.getElementById('pageUrl').value = window.location.href;</script>'''


def get_calc_name(html):
    m = re.search(r'<link rel="canonical" href="https://calccover\.com/([^/]+)/"', html)
    if m:
        slug = m.group(1)
        return slug.replace("-", " ").title()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return "Calccover Calculator"


def patch_file(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    original = html

    # Skip if already Web3Forms
    if "api.web3forms.com" in html:
        print(f"  Already Web3Forms: {path}")
        return False

    # Find the entire form block from <form action="https://formsubmit.co/..." to </form>
    pattern = re.compile(
        r'<form action="https://formsubmit\.co/[^"]*"[^>]*>.*?</form>(\s*<script[^>]*>document\.getElementById\([\'"]pageUrl[\'"]\)[^<]*</script>)?',
        re.DOTALL | re.IGNORECASE
    )

    match = pattern.search(html)
    if not match:
        print(f"  No FormSubmit form found: {path}")
        return False

    name = get_calc_name(html)
    new_form = FORM_TEMPLATE.replace("{ACCESS_KEY}", ACCESS_KEY).replace("{NAME}", name)
    html = html[:match.start()] + new_form + html[match.end():]

    if html != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✅ Patched: {path} — form name: {name}")
        return True
    return False


def main():
    print("Replacing FormSubmit with Web3Forms...\n")
    patched = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for file in files:
            if file != "index.html":
                continue
            path = os.path.join(root, file)
            if path == "./index.html":
                continue
            try:
                if patch_file(path):
                    patched += 1
            except Exception as e:
                print(f"  ❌ Error on {path}: {e}")
    print(f"\nDone. Patched: {patched}")


if __name__ == "__main__":
    main()
