#!/usr/bin/env python3
"""
Reformat FAQ answers into:
- 30-45 word "Short answer:" (visible, prime real estate for AI citation)
- Remaining detail below

Handles BOTH formats:
1. <details><summary>Q</summary><p>A</p></details>
2. <h3>Q</h3><p>A</p>

Idempotent — skips answers already reformatted.
Preview mode: --preview <file> to test on one file first.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Lower thresholds — answers >= 55 words get split
MIN_WORDS_TO_SPLIT = 50
DIRECT_ANSWER_TARGET = 40  # aim for 40-word short answers


def strip_html(html):
    return re.sub(r"<[^>]+>", "", html).strip()


def word_count(text):
    return len(text.split())


def split_sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p.strip()]


def build_split(text, target_words=DIRECT_ANSWER_TARGET):
    """Return (short_answer, detail). Either may be empty."""
    sentences = split_sentences(text)
    if not sentences:
        return "", ""

    short = ""
    for s in sentences:
        candidate = (short + " " + s).strip() if short else s
        if word_count(candidate) <= target_words + 15:  # allow up to 55 words
            short = candidate
        else:
            break

    if not short:
        short = sentences[0]

    remaining = " ".join(sentences[len(split_sentences(short)):]).strip()
    return short, remaining


def reformat_answer(answer_text):
    """
    Returns (new_inner_html, changed).
    answer_text is the plain text (no tags) of the answer.
    """
    wc = word_count(answer_text)

    if wc < MIN_WORDS_TO_SPLIT:
        return None, False

    short, detail = build_split(answer_text)

    if not short or not detail:
        return None, False

    if word_count(short) < 20:
        return None, False

    new_html = f'<strong>Short answer:</strong> {short}</p>\n<p>{detail}'
    return new_html, True


def process_file(filepath, preview=False):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = 0

    # ---------- Format 1: <details> ----------
    def replace_details(match):
        nonlocal changes
        block = match.group(0)

        summary_end = block.find("</summary>")
        if summary_end == -1:
            return block

        # Skip non-FAQ details blocks (e.g. "How this calculator works")
        summary_text = strip_html(block[:summary_end]).lower()
        if summary_text.startswith("how this") or summary_text.startswith("how our"):
            return block

        after = block[summary_end + len("</summary>"):]
        details_close = after.rfind("</details>")
        inner = after[:details_close] if details_close != -1 else after

        p_match = re.search(r"<p[^>]*>(.*?)</p>", inner, re.DOTALL)
        if not p_match:
            return block

        answer_html = p_match.group(1)
        answer_text = strip_html(answer_html)

        new_inner, changed = reformat_answer(answer_text)
        if changed:
            changes += 1
            new_block = block.replace(
                p_match.group(0),
                f"<p>{new_inner}</p>",
                1,
            )
            return new_block
        return block

    content = re.sub(
        r"<details[^>]*>.*?</details>",
        replace_details,
        content,
        flags=re.DOTALL,
    )

    # ---------- Format 2: <h3>Q?</h3> followed by <p>A</p> ----------
    def replace_h3(match):
        nonlocal changes
        h3_tag = match.group(1)
        answer_html = match.group(2)
        answer_text = strip_html(answer_html)

        new_inner, changed = reformat_answer(answer_text)
        if changed:
            changes += 1
            return f"{h3_tag}<p>{new_inner}</p>"
        return match.group(0)

    # Match: <h3>Q?</h3> whitespace <p>...</p>
    content = re.sub(
        r"(<h3>[^<]*\?</h3>\s*)<p>(.*?)</p>",
        replace_h3,
        content,
        flags=re.DOTALL,
    )

    if content != original:
        if not preview:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        return changes

    return 0


def preview_file(rel_path):
    filepath = os.path.join(ROOT, rel_path)
    if not os.path.exists(filepath):
        print(f"ERROR: {filepath} not found")
        return

    print(f"\n=== PREVIEW: {rel_path} ===\n")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Show first 3 details FAQs
    details = re.findall(r"<details[^>]*>.*?</details>", content, re.DOTALL)
    print(f"Found {len(details)} <details> blocks")
    for i, block in enumerate(details[:2]):
        summary_match = re.search(r"<summary>(.*?)</summary>", block, re.DOTALL)
        p_match = re.search(r"<p[^>]*>(.*?)</p>", block, re.DOTALL)
        if summary_match and p_match:
            q = strip_html(summary_match.group(1))
            a = strip_html(p_match.group(1))
            print(f"\n[FAQ {i+1}]")
            print(f"Q: {q[:80]}")
            print(f"A word count: {word_count(a)}")
            if word_count(a) >= MIN_WORDS_TO_SPLIT:
                short, detail = build_split(a)
                print(f"\n  SHORT ({word_count(short)} words): {short}")
                print(f"\n  DETAIL ({word_count(detail)} words): {detail[:200]}...")
            else:
                print(f"  → Skipped (under {MIN_WORDS_TO_SPLIT} words)")

    # Show first 2 h3 FAQs
    h3_matches = re.findall(r"(<h3>[^<]*\?</h3>\s*)<p>(.*?)</p>", content, re.DOTALL)
    print(f"\nFound {len(h3_matches)} <h3> FAQ blocks")
    for i, (h3_tag, ans) in enumerate(h3_matches[:2]):
        q = strip_html(h3_tag)
        a = strip_html(ans)
        print(f"\n[FAQ {i+1}]")
        print(f"Q: {q[:80]}")
        print(f"A word count: {word_count(a)}")
        if word_count(a) >= MIN_WORDS_TO_SPLIT:
            short, detail = build_split(a)
            print(f"\n  SHORT ({word_count(short)} words): {short}")
            print(f"\n  DETAIL ({word_count(detail)} words): {detail[:200]}...")
        else:
            print(f"  → Skipped (under {MIN_WORDS_TO_SPLIT} words)")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        preview_file(sys.argv[2])
        return

    total_files = 0
    total_faqs = 0

    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "scripts", "node_modules")]
        if "index.html" not in files:
            continue
        filepath = os.path.join(root, "index.html")
        rel = os.path.relpath(filepath, ROOT).replace("\\", "/")

        changes = process_file(filepath)
        if changes > 0:
            print(f"  OK  {rel}  [{changes} FAQ{'s' if changes != 1 else ''}]")
            total_files += 1
            total_faqs += changes

    print(f"\nReformatted {total_faqs} FAQ answers across {total_files} files.")


if __name__ == "__main__":
    main()