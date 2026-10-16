#!/usr/bin/env python3
"""
Reformat FAQ answers > 80 words into:
- A 40-60 word direct answer (visible)
- The remaining detail (collapsible)

Idempotent — skips answers already reformatted.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIRECT_ANSWER_MIN = 40
DIRECT_ANSWER_MAX = 60


def split_into_sentences(text):
    """Split text into sentences while keeping punctuation."""
    # Split on . ! ? followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p.strip()]


def build_direct_answer(text, target_words=50):
    """Return the first sentences up to ~target_words words."""
    sentences = split_into_sentences(text)
    if not sentences:
        return text, ""

    direct = ""
    for s in sentences:
        candidate = (direct + " " + s).strip()
        if len(candidate.split()) <= DIRECT_ANSWER_MAX:
            direct = candidate
        else:
            break

    # If we couldn't fit even one sentence, use the first one anyway
    if not direct:
        direct = sentences[0]

    remaining = text[len(direct):].strip()
    return direct, remaining


def reformat_answer(answer_html):
    """
    Take the content of a <p> inside a FAQ <details> block.
    If it's > 80 words, split it.
    Returns (new_html, changed).
    """
    # Strip HTML tags to count words
    text = re.sub(r"<[^>]+>", "", answer_html)
    word_count = len(text.split())

    if word_count <= 80:
        return answer_html, False

    # Already reformatted?
    if "<strong>Short answer:" in answer_html:
        return answer_html, False

    # Split into direct + detail
    direct, detail = build_direct_answer(text, target_words=50)

    if not detail:
        return answer_html, False

    new_html = f'<p><strong>Short answer:</strong> {direct}</p>\n<p>{detail}</p>'

    return new_html, True


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = 0

    # Match each <details>...</details> block
    def replace_details(match):
        nonlocal changes
        block = match.group(0)

        # Find the answer <p> inside (the one after </summary>)
        summary_end = block.find("</summary>")
        if summary_end == -1:
            return block

        # Get the content after </summary> and before </details>
        inner = block[summary_end + len("</summary>"):block.rfind("</details>")]

        # Find the first <p>...</p> in inner
        p_match = re.search(r"<p[^>]*>(.*?)</p>", inner, re.DOTALL)
        if not p_match:
            return block

        answer_html = p_match.group(1)
        new_answer, changed = reformat_answer(answer_html)

        if changed:
            changes += 1
            new_inner = inner.replace(p_match.group(0), new_answer, 1)
            return block[:summary_end + len("</summary>")] + new_inner + "</details>"

        return block

    content = re.sub(r"<details[^>]*>.*?</details>", replace_details, content, flags=re.DOTALL)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return changes

    return 0


def main():
    total_files = 0
    total_faqs = 0

    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "scripts", "node_modules")]
        if "index.html" not in files:
            continue

        filepath = os.path.join(root, "index.html")
        rel = os.path.relpath(filepath, ROOT).replace("\\", "/")

        # Only process calculator, hub, and blog pages (not state pages — those don't have FAQs in same format)
        if not (rel.endswith("index.html") and (
            "calculator" in rel or
            "insurance" in rel or
            rel.startswith("best/") or
            rel.startswith("compare/") or
            rel == "index.html" or
            "commercial-insurance" in rel or
            "blog/" in rel
        )):
            continue

        changes = process_file(filepath)
        if changes > 0:
            print(f"  OK  {rel}  [{changes} FAQ{'s' if changes != 1 else ''}]")
            total_files += 1
            total_faqs += changes

    print(f"\nReformatted {total_faqs} FAQ answers across {total_files} files.")


if __name__ == "__main__":
    main()
