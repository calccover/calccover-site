#!/usr/bin/env python3
"""
Sync FAQPage schema markup to match reformatted visible FAQ answers.

For each page that has <strong>Short answer:</strong> in the visible HTML,
update the corresponding FAQPage JSON-LD schema so the answer text matches.

Idempotent — safe to run multiple times.
"""
import os
import re
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip_html(html):
    return re.sub(r"<[^>]+>", " ", html)


def clean_text(text):
    """Collapse whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def extract_visible_faqs(content):
    """
    Extract visible FAQ Q&A pairs from the page.
    Returns dict: {question: answer_text}
    Handles both <details> and <h3> formats.
    """
    faqs = {}

    # Format 1: <details>
    for match in re.finditer(r"<details[^>]*>.*?</details>", content, re.DOTALL):
        block = match.group(0)
        summary_match = re.search(r"<summary>(.*?)</summary>", block, re.DOTALL)
        if not summary_match:
            continue
        q = clean_text(strip_html(summary_match.group(1)))

        # Skip "How this calculator works"
        if q.lower().startswith("how this"):
            continue

        # Get the answer inside <p>...</p>
        after = block[summary_match.end():]
        p_matches = re.findall(r"<p[^>]*>(.*?)</p>", after, re.DOTALL)
        if not p_matches:
            continue
        answer_html = " ".join(p_matches)
        a = clean_text(strip_html(answer_html))
        faqs[q] = a

    # Format 2: <h3>Q?</h3><p>A</p>
    for match in re.finditer(r"<h3>([^<]*\?)</h3>\s*<p>(.*?)</p>", content, re.DOTALL):
        q = clean_text(strip_html(match.group(1)))
        a = clean_text(strip_html(match.group(2)))
        faqs[q] = a

    return faqs


def update_schema(content, faqs):
    """Update the FAQPage schema JSON-LD to match visible FAQs."""
    changes = 0

    def replace_schema(match):
        nonlocal changes
        schema_json = match.group(1)

        try:
            data = json.loads(schema_json)
        except json.JSONDecodeError:
            return match.group(0)

        if data.get("@type") != "FAQPage":
            return match.group(0)

        main_entity = data.get("mainEntity", [])
        if not main_entity:
            return match.group(0)

        for entry in main_entity:
            if entry.get("@type") != "Question":
                continue

            q_text = clean_text(strip_html(entry.get("name", "")))
            visible = faqs.get(q_text)

            if not visible:
                continue

            # Normalize visible answer for schema:
            # replace "Short answer: " prefix and collapse into one string
            normalized = visible.replace("Short answer: ", "Short answer: ").strip()

            old_answer = entry.get("acceptedAnswer", {}).get("text", "")
            if old_answer.strip() != normalized:
                entry["acceptedAnswer"]["text"] = normalized
                changes += 1

        # Rebuild the script tag with pretty-printed JSON
        new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f'<script type="application/ld+json">{new_json}</script>'

    content = re.sub(
        r'<script type="application/ld\+json">(.*?)</script>',
        replace_schema,
        content,
        flags=re.DOTALL,
    )

    return content, changes


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip files with no reformatted answers
    if "<strong>Short answer:</strong>" not in content:
        return 0

    faqs = extract_visible_faqs(content)
    if not faqs:
        return 0

    new_content, changes = update_schema(content, faqs)

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return changes

    return 0


def main():
    total_files = 0
    total_updates = 0

    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "scripts", "node_modules")]
        if "index.html" not in files:
            continue
        filepath = os.path.join(root, "index.html")
        rel = os.path.relpath(filepath, ROOT).replace("\\", "/")

        changes = process_file(filepath)
        if changes > 0:
            print(f"  OK  {rel}  [{changes} schema FAQ{'s' if changes != 1 else ''} updated]")
            total_files += 1
            total_updates += changes

    print(f"\nSynced {total_updates} FAQ schema entries across {total_files} files.")


if __name__ == "__main__":
    main()