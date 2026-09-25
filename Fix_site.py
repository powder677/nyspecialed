#!/usr/bin/env python3
"""
Cleans up nav + promo clutter across every HTML page in the site.

What it does on every page it finds these on:
  1. Removes the "Upstate Districts" nav link/tab (desktop + mobile,
     in both the flat-link nav and the older dropdown nav).
  2. Renames the "NYC Districts" nav tab to just "Districts"
     (desktop + mobile, flat and dropdown nav).
  3. Removes the "Get Your IEP Letter Written by our AI Bot" promo
     banner — wherever it appears on the page (top, bottom, or both).
  4. Removes the "IEP Letter Writer" offer box in the right sidebar.

Usage:
    python remove_nav_items.py /path/to/site/root --dry-run   # preview
    python remove_nav_items.py /path/to/site/root             # apply
"""

import argparse
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment


def norm(el):
    """Collapsed, lowercased text of an element."""
    return " ".join(el.get_text().split()).lower()


def top_level_only(matches):
    """Given a list of matched tags, drop any that are nested inside
    another match (so we remove the outermost container once, not its
    children too)."""
    match_ids = {id(m) for m in matches}
    result = []
    for m in matches:
        nested = False
        anc = m.parent
        while anc is not None:
            if id(anc) in match_ids:
                nested = True
                break
            anc = anc.parent
        if not nested:
            result.append(m)
    return result


def process_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    changes = []

    # ------------------------------------------------------------------
    # 1. Remove "Upstate Districts" nav link — flat-nav style:
    #    <li><a href="/districts/upstate/">Upstate Districts</a></li>
    #    and bare mobile version: <a href="/districts/upstate/">...</a>
    # ------------------------------------------------------------------
    for a in soup.find_all("a", href="/districts/upstate/"):
        li_parent = a.find_parent("li")
        if li_parent:
            li_parent.decompose()
        else:
            a.decompose()
        changes.append("Removed 'Upstate Districts' nav link")

    # 1b. Dropdown-nav style: <li class="nav-item"><button>Upstate & LI ▼</button>...</li>
    for li in soup.select("li.nav-item"):
        btn = li.find("button", class_="nav-link")
        if btn and "upstate" in norm(btn):
            li.decompose()
            changes.append("Removed 'Upstate & LI' dropdown nav item")

    # 1c. Dropdown-nav mobile section: <div class="mobile-section-head">Upstate & LI</div>
    #     followed by its links, up to the next section head.
    for head in soup.select(".mobile-section-head"):
        if "upstate" in norm(head):
            to_remove = [head]
            for sib in head.find_next_siblings():
                classes = sib.get("class", []) if hasattr(sib, "get") else []
                if "mobile-section-head" in classes:
                    break
                to_remove.append(sib)
            for el in to_remove:
                el.decompose()
            changes.append("Removed 'Upstate & LI' mobile nav section")

    # ------------------------------------------------------------------
    # 2. Rename "NYC Districts" tab -> "Districts"
    # ------------------------------------------------------------------
    for tag in soup.find_all(["a", "button"]):
        text = " ".join(tag.get_text().split())
        if text == "NYC Districts":
            tag.string = "Districts"
            changes.append("Renamed 'NYC Districts' -> 'Districts'")
        elif text == "NYC Districts \u25bc":  # "NYC Districts ▼"
            tag.string = "Districts \u25bc"
            changes.append("Renamed 'NYC Districts ▼' -> 'Districts ▼'")

    # ------------------------------------------------------------------
    # 3. Remove "Get Your IEP Letter Written by our AI Bot" promo banner(s)
    #    Match: a div containing "iep letter" text AND a link mentioning
    #    "$15" or "start now" — catches both a top and a bottom copy.
    # ------------------------------------------------------------------
    banner_candidates = []
    for div in soup.find_all("div"):
        text = norm(div)
        if "iep letter" not in text:
            continue
        link = div.find("a")
        if link and ("$15" in link.get_text() or "start now" in norm(link)):
            banner_candidates.append(div)
    for div in top_level_only(banner_candidates):
        div.decompose()
        changes.append("Removed IEP Letter promo banner")

    # ------------------------------------------------------------------
    # 4. Remove "IEP Letter Writer" sidebar offer box (right margin)
    # ------------------------------------------------------------------
    sidebar_candidates = []
    for div in soup.find_all("div", class_="premium-sidebar-right"):
        if "letter writer" in norm(div):
            sidebar_candidates.append(div)
    # Fallback in case the class name isn't present but the box still is:
    if not sidebar_candidates:
        for h3 in soup.find_all(["h3", "h4"]):
            if "iep letter writer" in norm(h3):
                # walk up to a reasonably-sized container
                container = h3.find_parent("div")
                if container:
                    sidebar_candidates.append(container)
    for div in top_level_only(sidebar_candidates):
        div.decompose()
        changes.append("Removed 'IEP Letter Writer' sidebar offer")

    # ------------------------------------------------------------------
    # Cleanup: orphaned comments left behind next to removed blocks
    # ------------------------------------------------------------------
    if changes:
        for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
            low = c.lower()
            if "upstate" in low or "top banner" in low or "bottom banner" in low:
                c.extract()

    return soup, changes


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
            total_changed += 1
            print(f"\n{path}")
            for c in changes:
                print(f"  - {c}")
            if not args.dry_run:
                path.write_text(str(soup), encoding="utf-8")

    print(f"\n{'Would update' if args.dry_run else 'Updated'} "
          f"{total_changed} of {len(html_files)} HTML file(s).")


if __name__ == "__main__":
    main()