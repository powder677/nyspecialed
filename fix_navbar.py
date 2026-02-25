#!/usr/bin/env python3
"""
STEP 1: Run without --fix to see what's in your navbar across all pages.
STEP 2: Run with --fix to inject the correct logo into every HTML page.

Usage:
    python fix_navbar.py              (scan and preview)
    python fix_navbar.py --fix        (apply to all pages)
    python fix_navbar.py --dir "C:\\path"
"""

import re
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_PROJECT_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"

# The correct logo HTML to use everywhere
CORRECT_LOGO = '''<a href="/" class="nav-logo" aria-label="New York Special Ed - Home">
         <img src="/images/logo.png" alt="New York Special Ed logo" width="50" height="50" loading="eager" style="display:block; height:50px; width:auto; border-radius:8px;" />
      </a>'''

SKIP_DIRS = {
    ".git", "node_modules", ".next", "dist", "build",
    ".cache", "__pycache__", ".svelte-kit", ".vercel", ".netlify",
}

# ── Patterns ──────────────────────────────────────────────────────────────────

# Finds ANY existing logo anchor in the navbar - correct or broken
# Matches <a ... class="nav-logo" ...> ... </a>  (with nested img)
LOGO_TAG_PATTERN = re.compile(
    r'<a[^>]*class=["\'][^"\']*nav-logo[^"\']*["\'][^>]*>.*?</a>',
    re.IGNORECASE | re.DOTALL,
)

# Finds the bad plain-text domain reference used as a logo
BAD_DOMAIN_PATTERN = re.compile(
    r'(nyspecialed\.com|ny[\s\-_]*special[\s\-_]*ed\.com|newyorkspecialed\.com)',
    re.IGNORECASE,
)

# Finds any <nav> or <header> block so we can show context
NAV_PATTERN = re.compile(
    r'<(?:nav|header)[^>]*>.*?</(?:nav|header)>',
    re.IGNORECASE | re.DOTALL,
)

# ── Scanner ───────────────────────────────────────────────────────────────────

def scan_and_fix(project_dir: str, fix: bool = False):
    root = Path(project_dir)
    if not root.exists():
        print(f"[ERROR] Directory not found: {project_dir}")
        return

    pages_with_correct_logo  = []
    pages_with_broken_logo   = []
    pages_with_no_logo       = []
    pages_with_bad_domain    = []
    total_html               = 0

    print(f"\nScanning : {root}")
    print(f"Fix mode : {'YES - will update all pages' if fix else 'NO  - preview only'}")
    print("=" * 70)

    for path in sorted(root.rglob("*.html")):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        total_html += 1
        rel = path.relative_to(root)

        has_correct_logo = bool(LOGO_TAG_PATTERN.search(content))
        has_bad_domain   = bool(BAD_DOMAIN_PATTERN.search(content))
        nav_block        = NAV_PATTERN.search(content)

        print(f"\n  PAGE: {rel}")

        # Show what's in the nav/header
        if nav_block:
            snippet = nav_block.group(0).strip()
            # Just show first 200 chars so output is readable
            preview = snippet[:200] + ("..." if len(snippet) > 200 else "")
            print(f"   Nav/header found:")
            for line in preview.splitlines():
                print(f"     {line}")
        else:
            print(f"   No <nav> or <header> tag found")

        # Categorise
        if has_correct_logo:
            pages_with_correct_logo.append(rel)
            print(f"   [OK]  Logo tag found with class='nav-logo'")
        else:
            pages_with_no_logo.append(rel)
            print(f"   [!!]  No nav-logo tag found")

        if has_bad_domain:
            pages_with_bad_domain.append(rel)
            for m in BAD_DOMAIN_PATTERN.finditer(content):
                # Get surrounding context
                start = max(0, m.start() - 40)
                end   = min(len(content), m.end() + 40)
                ctx   = content[start:end].replace("\n", " ").strip()
                print(f"   [!!]  Bad domain in page: ...{ctx}...")

        # ── Apply fix ─────────────────────────────────────────────────────────
        if fix:
            updated = content

            if has_correct_logo:
                # Logo tag exists — replace it with the correct one
                updated, n = LOGO_TAG_PATTERN.subn(CORRECT_LOGO, updated)
                print(f"   --> Updated {n} existing logo tag(s)")

            elif nav_block:
                # No logo tag but there's a nav — inject logo at start of nav
                def inject_logo(m):
                    nav_html = m.group(0)
                    # Insert after the opening tag
                    open_tag_end = nav_html.index(">") + 1
                    return nav_html[:open_tag_end] + "\n      " + CORRECT_LOGO + "\n      " + nav_html[open_tag_end:]
                updated, n = NAV_PATTERN.subn(inject_logo, updated)
                print(f"   --> Injected logo into <nav>/<header>")

            else:
                print(f"   [SKIP] No <nav> or <header> found — cannot auto-inject. Add nav manually.")

            if updated != content:
                path.write_text(updated, encoding="utf-8")
                print(f"   --> Saved")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"\nSUMMARY  ({total_html} HTML files scanned)")
    print(f"  Pages with correct logo  : {len(pages_with_correct_logo)}")
    print(f"  Pages missing logo       : {len(pages_with_no_logo)}")
    print(f"  Pages with bad domain    : {len(pages_with_bad_domain)}")

    if pages_with_no_logo:
        print(f"\n  Pages needing logo fix:")
        for f in pages_with_no_logo:
            print(f"    [!!] {f}")

    if pages_with_bad_domain:
        print(f"\n  Pages with bad domain text:")
        for f in pages_with_bad_domain:
            print(f"    [!!] {f}")

    if not fix and (pages_with_no_logo or pages_with_bad_domain):
        print(f"\n  Run with --fix to update all pages:")
        print(f"  python fix_navbar.py --fix")
    elif fix:
        print(f"\n  All pages updated!")
        print(f"\n  IMPORTANT: Check one page in your browser to confirm the logo")
        print(f"  looks correct before deploying.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scan and fix navbar logo across all HTML pages."
    )
    parser.add_argument("--dir", default=DEFAULT_PROJECT_DIR)
    parser.add_argument("--fix", action="store_true",
                        help="Apply fixes to all pages")
    args = parser.parse_args()
    scan_and_fix(args.dir, fix=args.fix)


if __name__ == "__main__":
    main()