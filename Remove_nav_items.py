#!/usr/bin/env python3
"""
Removes two things from the site nav on every HTML page in a folder:
  1. The "Upstate & LI" nav item (desktop dropdown + its mobile menu section)
  2. The "IEP Letter" link (Generador de Carta IEP, in the Spanish nav dropdown)

Usage:
    python3 remove_nav_items.py /path/to/site/root
    python3 remove_nav_items.py /path/to/site/root --dry-run

By default it walks the given folder recursively and edits every .html file
in place. Use --dry-run to see what WOULD change without writing anything.
"""

import argparse
import sys
from pathlib import Path

from bs4 import BeautifulSoup

UPSTATE_TEXT = "upstate"
IEP_LETTER_MARKERS = ("carta iep", "iep letter")


def strip_text(el):
    return " ".join(el.get_text().split()).lower()


def process_html(html: str):
    """Returns (new_html, changes_made:list[str])"""
    soup = BeautifulSoup(html, "html.parser")
    changes = []

    # --- 1. Desktop nav item: <li class="nav-item"><button ...>Upstate & LI ▼</button>...</li>
    for li in soup.select("li.nav-item"):
        btn = li.find("button", class_="nav-link")
        if btn and UPSTATE_TEXT in strip_text(btn):
            li.decompose()
            changes.append("Removed desktop nav item: Upstate & LI")

    # --- 2. Mobile nav section: <div class="mobile-section-head">Upstate & LI</div>
    #        followed by <a> links up to (not including) the next section head.
    for head in soup.select(".mobile-section-head"):
        if UPSTATE_TEXT in strip_text(head):
            to_remove = [head]
            for sib in head.find_next_siblings():
                classes = sib.get("class", []) if hasattr(sib, "get") else []
                if "mobile-section-head" in classes:
                    break
                to_remove.append(sib)
            for el in to_remove:
                el.decompose()
            changes.append("Removed mobile nav section: Upstate & LI")

    # --- 3. IEP Letter link anywhere in the nav (e.g. "Generador de Carta IEP")
    for a in soup.find_all("a"):
        text = strip_text(a)
        if any(marker in text for marker in IEP_LETTER_MARKERS):
            a.decompose()
            changes.append(f"Removed IEP letter link: {text!r}")

    return soup, changes


def cleanup_stray_comments(soup):
    """Remove now-orphaned HTML comments like <!-- Upstate & LI --> that were
    left behind as markers next to a deleted block."""
    from bs4 import Comment
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        if "upstate" in c.lower():
            c.extract()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="Folder containing your HTML pages")
    parser.add_argument("--dry-run", action="store_true",
                         help="Show what would change without writing files")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Path not found: {root}")
        sys.exit(1)

    html_files = sorted(root.rglob("*.html"))
    if not html_files:
        print(f"No .html files found under {root}")
        sys.exit(0)

    total_changed = 0
    for path in html_files:
        original = path.read_text(encoding="utf-8")
        soup, changes = process_html(original)
        if changes:
            cleanup_stray_comments(soup)
            total_changed += 1
            print(f"\n{path}")
            for c in changes:
                print(f"  - {c}")
            if not args.dry_run:
                path.write_text(str(soup), encoding="utf-8")
        # files with no nav match are left completely untouched (silent)

    print(f"\n{'Would update' if args.dry_run else 'Updated'} "
          f"{total_changed} of {len(html_files)} HTML file(s).")


if __name__ == "__main__":
    main()