#!/usr/bin/env python3
"""
Patch header and footer nav across all Calccover pages.

Adds "Blog" link to header nav and footer on every index.html.
Handles both footer variants used on the site (calculator vs. article).
Idempotent — safe to run multiple times. Running twice does nothing.

Usage:
    python scripts/patch_header_footer.py --dry-run
    python scripts/patch_header_footer.py
"""
import os
import re
import sys
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# New header nav (with Blog first)
NEW_HEADER_NAV = (
    '<nav><a href="/blog/">Blog</a>'
    '<a href="/how-it-works/">How It Works</a>'
    '<a href="/about/">About</a>'
    '<a href="/contact/">Contact</a></nav>'
)

# Footer "Blog" link, styled for calculator pages (has inline styles)
FOOTER_BLOG_STYLED = (
    '<a href="/blog/" style="margin-right:1.5rem;color:#555;text-decoration:none">Blog</a>'
)

# Footer "Blog" link, unstyled (article/pillar pages)
FOOTER_BLOG_PLAIN = '<a href="/blog/">Blog</a>'


def patch_header(content: str) -> tuple[str, bool]:
    """Insert Blog link into header nav. Returns (new_content, changed)."""
    nav_match = re.search(r'<nav>(.*?)</nav>', content, re.DOTALL)
    if not nav_match:
        return content, False

    nav_inner = nav_match.group(1)
    if '<a href="/blog/">' in nav_inner:
        return content, False  # already patched

    # Rebuild nav with Blog first
    new_nav = NEW_HEADER_NAV
    return content[:nav_match.start()] + new_nav + content[nav_match.end():], True


def patch_footer(content: str) -> tuple[str, bool]:
    """Insert Blog link after Home in footer. Returns (new_content, changed)."""
    footer_match = re.search(r'<footer>.*?</footer>', content, re.DOTALL)
    if not footer_match:
        return content, False

    footer = footer_match.group(0)
    if '<a href="/blog/">' in footer:
        return content, False  # already patched

    # Detect which variant: styled or plain
    # Variant A (calculator): Home link has style attribute
    if re.search(r'<a href="/" style="[^"]*">Home</a>', footer):
        new_footer = re.sub(
            r'(<a href="/" style="[^"]*">Home</a>)',
            r'\1\n            ' + FOOTER_BLOG_STYLED,
            footer,
            count=1,
        )
    # Variant B (article): plain Home link
    elif re.search(r'<a href="/">Home</a>', footer):
        new_footer = re.sub(
            r'(<a href="/">Home</a>)',
            r'\1\n            ' + FOOTER_BLOG_PLAIN,
            footer,
            count=1,
        )
    else:
        return content, False

    if new_footer == footer:
        return content, False

    return content.replace(footer, new_footer, 1), True


def patch_file(filepath: str, dry_run: bool = False) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    content = original
    header_changed = False
    footer_changed = False

    content, header_changed = patch_header(content)
    content, footer_changed = patch_footer(content)

    if not (header_changed or footer_changed):
        return {'status': 'skipped', 'header': False, 'footer': False}

    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return {
        'status': 'patched',
        'header': header_changed,
        'footer': footer_changed,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would change without writing files')
    parser.add_argument('--verbose', action='store_true',
                        help='Show skipped files too')
    args = parser.parse_args()

    patched = 0
    skipped = 0
    errors = 0
    header_count = 0
    footer_count = 0

    for root, dirs, files in os.walk(ROOT):
        # Skip non-content directories
        dirs[:] = [d for d in dirs if d not in (
            '.git', 'node_modules', '.github', 'scripts',
            '.next', 'dist', 'out', 'build'
        )]

        if 'index.html' not in files:
            continue

        filepath = os.path.join(root, 'index.html')
        rel = os.path.relpath(filepath, ROOT).replace('\\', '/')

        try:
            result = patch_file(filepath, dry_run=args.dry_run)
            if result['status'] == 'patched':
                parts = []
                if result['header']:
                    parts.append('header')
                    header_count += 1
                if result['footer']:
                    parts.append('footer')
                    footer_count += 1
                print(f'  OK  {rel}  [{", ".join(parts)}]')
                patched += 1
            else:
                if args.verbose:
                    print(f'  --  {rel}  (already patched)')
                skipped += 1
        except Exception as e:
            print(f'  ERR {rel}  {e}')
            errors += 1

    print()
    print(f'{"[DRY RUN] " if args.dry_run else ""}Results:')
    print(f'  Patched:           {patched}')
    print(f'  Header updates:    {header_count}')
    print(f'  Footer updates:    {footer_count}')
    print(f'  Already up to date: {skipped}')
    print(f'  Errors:            {errors}')

    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
