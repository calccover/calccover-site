#!/usr/bin/env python3
"""
Calccover — One-time patch script.
Replaces the old placeholder lead form + submitLead() with FormSubmit integration.
"""
import os
import re
import sys

# Folders to skip
SKIP = {"scripts", ".github", "about", "contact", "privacy", "terms", "thank-you", "node_modules", "assets", "images"}

NEW_FORM = '''<form action="https://formsubmit.co/hello@calccover.com" method="POST">
    <input type="email" name="email" required placeholder="your@email.com">
    <input type="hidden" name="calculator" value="__NAME__">
    <input type="hidden" name="page_url" id="pageUrl" value="">
    <input type="hidden" name="_subject" value="New quote request — __NAME__">
    <input type="hidden" name="_captcha" value="false">
    <input type="hidden" name="_next" value="https://calccover.com/thank-you/">
    <button type="submit">Get a Free Quote</button>
</form>
<script>document.getElementById('pageUrl').value = window.location.href;</script>'''


def extract_h1(html):
    """Try to get a page-specific name from the H1 or the canonical URL."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r'<link rel="canonical" href="https://calccover\.com/([^/]+)/"', html)
    if m:
        return m.group(1).replace("-", " ").title()
    return "Calccover Calculator"


def patch_file(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    original = html
    page_name = extract_h1(html)
    new_form = NEW_FORM.replace("__NAME__", page_name)

    # Pattern 1: Button inside a lead-form div that calls submitLead
    # Match the button and replace the whole enclosing form/div area
    pattern_old_button = re.compile(
        r'<button[^>]*onclick="submitLead\(\)"[^>]*>.*?</button>',
        re.DOTALL | re.IGNORECASE
    )

    # Replace the button + the email input it was tied to
    # Match: email input followed by button
    pattern_input_button = re.compile(
        r'<input[^>]*id="leadEmail"[^>]*>\s*<button[^>]*onclick="submitLead\(\)"[^>]*>[^<]*</button>',
        re.DOTALL | re.IGNORECASE
    )

    if pattern_input_button.search(html):
        html = pattern_input_button.sub(new_form, html)
    elif pattern_old_button.search(html):
        # Just replace the button if we can't find the input
        html = pattern_old_button.sub(new_form, html)
    else:
        print(f"  No old form pattern found in {path} — skipping")
        return False

    # Remove the submitLead() function
    html = re.sub(
        r'\n\s*function submitLead\s*\(\s*\)\s*\{[^}]*\}[^\n]*',
        '',
        html,
        flags=re.DOTALL
    )

    if html != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Patched: {path}")
        return True
    print(f"  No change needed: {path}")
    return False


def main():
    patched = 0
    skipped = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for file in files:
            if file != "index.html":
                continue
            path = os.path.join(root, file)
            if path == "./index.html":
                continue  # Skip homepage
            if patch_file(path):
                patched += 1
            else:
                skipped += 1
    print(f"\nDone. Patched: {patched}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
