#!/usr/bin/env python3
"""
fix_district_links.py
=====================
Fixes systematic linking bugs across all NYC/NYS district pages.

BUGS FIXED:
  1. District subnav tabs — all point to district root instead of their subpage
  2. Hub cards (index.html) — all point to district root instead of their subpage
  3. Stray .hub-card inside .footer-bottom — removed
  4. .subnav-active on wrong tab — corrected per page

DISTRICT DISCOVERY:
  Reads slug list from districts/index.html JavaScript array automatically.
  Falls back to scanning subfolders if the JS array isn't found.

USAGE:
  # Dry run — shows every change, writes nothing:
  python fix_district_links.py --root ./districts

  # Apply fixes in-place:
  python fix_district_links.py --root ./districts --write

  # Write to a separate folder (safe, non-destructive):
  python fix_district_links.py --root ./districts --write --out-dir ./districts_fixed

  # Fix a single district only:
  python fix_district_links.py --root ./districts/nyc-district-07-south-bronx --write

  # See every individual link change:
  python fix_district_links.py --root ./districts --write --verbose

REQUIREMENTS: pip install beautifulsoup4 lxml
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing dependency:  pip install beautifulsoup4 lxml")


# ── Label → filename mappings ─────────────────────────────────────────────────
# First match wins, so put more-specific keys first.

SUBNAV_MAP: list[tuple[str, str]] = [
    ("cse guide",       "cse-meeting-guide.html"),
    ("cse",             "cse-meeting-guide.html"),
    ("evaluations",     "evaluation-process.html"),
    ("evaluation",      "evaluation-process.html"),
    ("discipline",      "discipline-rights.html"),
    ("contacts",        "leadership-directory.html"),
    ("directory",       "leadership-directory.html"),
    ("partners",        "partners.html"),
    ("providers",       "partners.html"),
    ("updates",         "special-ed-updates.html"),
    ("advocacy guide",  "parent-advocacy-guide.html"),
    ("advocacy",        "parent-advocacy-guide.html"),
    ("support",         "partners.html"),
    ("hub",             "index.html"),
]

HUB_CARD_MAP: list[tuple[str, str]] = [
    ("cse guide",       "cse-meeting-guide.html"),
    ("cse",             "cse-meeting-guide.html"),
    ("evaluations",     "evaluation-process.html"),
    ("evaluation",      "evaluation-process.html"),
    ("discipline",      "discipline-rights.html"),
    ("contacts",        "leadership-directory.html"),
    ("directory",       "leadership-directory.html"),
    ("partners",        "partners.html"),
    ("providers",       "partners.html"),
    ("updates",         "special-ed-updates.html"),
    ("advocacy",        "parent-advocacy-guide.html"),
    ("support",         "partners.html"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def strip_emoji(text: str) -> str:
    return re.sub(
        "["
        "\U0001F300-\U0001FFFF"
        "\U00002702-\U000027B0"
        "\u2600-\u26FF"
        "\U0001F1E0-\U0001F1FF"
        "]+",
        "",
        text,
        flags=re.UNICODE,
    ).strip().lower()


def match_label(raw: str, mapping: list[tuple[str, str]]) -> str | None:
    norm = strip_emoji(raw)
    for key, fn in mapping:
        if key in norm:
            return fn
    return None


def build_url(root: str, filename: str) -> str:
    r = root.rstrip("/") + "/"
    return r if filename == "index.html" else r + filename


def read_canonical(path: Path) -> str | None:
    """Fast regex read of <link rel='canonical'> without full parse."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    for pattern in [
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def get_district_root_url(district_dir: Path) -> str | None:
    """
    Derive the canonical root URL for a district folder, e.g.
      https://www.newyorkspecialed.net/districts/nyc-district-07-south-bronx/

    Strategy (in order):
    1. index.html canonical ending in '/' that contains 'districts/'
    2. Any other .html canonical containing 'districts/' → strip filename
    3. Infer from folder name using a known base URL
    """
    index = district_dir / "index.html"
    if index.exists():
        url = read_canonical(index)
        if url and url.endswith("/") and "districts/" in url:
            return url

    for p in sorted(district_dir.glob("*.html")):
        if p.name == "index.html":
            continue
        url = read_canonical(p)
        if url and "districts/" in url:
            if url.endswith(".html"):
                return url.rsplit("/", 1)[0] + "/"
            if url.endswith("/"):
                return url

    # Fallback: construct from folder name
    return f"https://www.newyorkspecialed.net/districts/{district_dir.name}/"


# ── District slug discovery ───────────────────────────────────────────────────

def discover_slugs_from_index(districts_root: Path) -> list[str] | None:
    """
    Read district slugs from the JavaScript array in districts/index.html.
    Returns a list of slug strings, or None if not found.
    """
    index = districts_root / "index.html"
    if not index.exists():
        return None
    try:
        text = index.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    # Match:  const districts = [{"name": "...", "slug": "...", "type": "..."},...]
    m = re.search(r"const\s+districts\s*=\s*(\[.*?\]);", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
        return [d["slug"] for d in data if "slug" in d]
    except (json.JSONDecodeError, KeyError):
        return None


def discover_district_dirs(districts_root: Path) -> list[Path]:
    """
    Return list of district subdirectory Paths to process.
    Reads slugs from districts/index.html JS array first;
    falls back to scanning all subdirectories that contain *.html files.
    """
    slugs = discover_slugs_from_index(districts_root)

    if slugs:
        dirs = []
        missing = []
        for slug in slugs:
            d = districts_root / slug
            if d.is_dir():
                dirs.append(d)
            else:
                missing.append(slug)
        if missing:
            print(f"\n  ℹ  {len(missing)} slug(s) in index.html have no folder yet "
                  f"(skipped): {', '.join(missing[:5])}"
                  + (" …" if len(missing) > 5 else ""))
        print(f"  ✓  Found {len(dirs)} district folder(s) via districts/index.html JS array.")
        return sorted(dirs)

    # Fallback: scan subdirectories
    dirs = sorted(
        d for d in districts_root.iterdir()
        if d.is_dir() and list(d.glob("*.html"))
    )
    print(f"  ✓  Found {len(dirs)} district folder(s) by scanning subdirectories.")
    return dirs


# ── Fix functions ─────────────────────────────────────────────────────────────

def fix_subnav(soup: BeautifulSoup, root: str, verbose: bool) -> int:
    changes = 0
    for nav in soup.select("nav.district-subnav, .district-subnav"):
        for a in nav.find_all("a", href=True):
            fn = match_label(a.get_text(), SUBNAV_MAP)
            if fn is None:
                if verbose:
                    print(f"          ⚠  subnav no-match: '{a.get_text().strip()}'")
                continue
            correct = build_url(root, fn)
            if a["href"] != correct:
                if verbose:
                    print(f"          subnav '{a.get_text().strip()}'"
                          f"\n            {a['href']!r}"
                          f"\n            → {correct!r}")
                a["href"] = correct
                changes += 1
    return changes


def fix_hub_cards(soup: BeautifulSoup, root: str, verbose: bool) -> int:
    changes = 0

    # Remove stray hub-cards from .footer-bottom
    for fb in soup.select(".footer-bottom"):
        for card in fb.select("a.hub-card, .hub-card"):
            if verbose:
                print(f"          ⚠  Removed stray hub-card from .footer-bottom")
            card.decompose()
            changes += 1

    # Fix hub-grid cards
    for card in soup.select("a.hub-card"):
        heading = card.find(["h2", "h3", "h4"])
        if not heading:
            continue
        fn = match_label(heading.get_text(), HUB_CARD_MAP)
        if fn is None:
            if verbose:
                print(f"          ⚠  hub-card no-match: '{heading.get_text().strip()}'")
            continue
        correct = build_url(root, fn)
        if card.get("href") != correct:
            if verbose:
                print(f"          hub-card '{heading.get_text().strip()}'"
                      f"\n            {card.get('href')!r}"
                      f"\n            → {correct!r}")
            card["href"] = correct
            changes += 1
    return changes


def fix_active_tab(soup: BeautifulSoup, root: str,
                   current_file: str, verbose: bool) -> int:
    """Ensure .subnav-active is on exactly the tab for this page."""
    changes = 0
    current_url = build_url(root, current_file)

    for nav in soup.select("nav.district-subnav, .district-subnav"):
        for a in nav.find_all("a", href=True):
            is_current = (a["href"] == current_url)
            has_active = "subnav-active" in (a.get("class") or [])

            if is_current and not has_active:
                a["class"] = (a.get("class") or []) + ["subnav-active"]
                a["aria-current"] = "page"
                changes += 1
            elif not is_current and has_active:
                a["class"] = [c for c in (a.get("class") or [])
                               if c != "subnav-active"]
                if "aria-current" in a.attrs:
                    del a["aria-current"]
                changes += 1
    return changes


# ── Per-file processor ────────────────────────────────────────────────────────

def process_file(
    html_path: Path,
    root: str,
    out_path: Path,
    write: bool,
    verbose: bool,
    dry_log: list,
) -> dict:
    stats = {"subnav": 0, "hub": 0, "active": 0}
    try:
        original = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"    ERROR reading {html_path.name}: {e}")
        return stats

    soup = BeautifulSoup(original, "lxml")

    if verbose:
        print(f"\n      📄 {html_path.name}")

    stats["subnav"] = fix_subnav(soup, root, verbose)
    stats["hub"]    = fix_hub_cards(soup, root, verbose)
    stats["active"] = fix_active_tab(soup, root, html_path.name, verbose)

    total = sum(stats.values())

    if total == 0:
        if verbose:
            print(f"        ✓ no changes")
        return stats

    if write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(str(soup), encoding="utf-8")
        dest = f"→ {out_path}" if out_path != html_path else "in-place"
        print(f"    ✅  {html_path.name:45s}  {total:>3} fix(es)  [{dest}]")
    else:
        dry_log.append((html_path, total))
        print(f"    →   {html_path.name:45s}  {total:>3} fix(es) pending")

    return stats


# ── Per-district processor ────────────────────────────────────────────────────

def process_district(
    district_dir: Path,
    write: bool,
    out_root: Path | None,
    verbose: bool,
    dry_log: list,
) -> dict:
    totals = {"subnav": 0, "hub": 0, "active": 0, "files": 0}

    root_url = get_district_root_url(district_dir)

    html_files = sorted(district_dir.glob("*.html"))
    if not html_files:
        return totals

    print(f"\n  {'─'*58}")
    print(f"  {district_dir.name}")
    print(f"  {root_url}")

    for html_path in html_files:
        if out_root:
            try:
                rel = html_path.relative_to(district_dir.parent)
            except ValueError:
                rel = Path(district_dir.name) / html_path.name
            out_path = out_root / rel
        else:
            out_path = html_path

        stats = process_file(html_path, root_url, out_path, write, verbose, dry_log)
        for k in ("subnav", "hub", "active"):
            totals[k] += stats[k]
        totals["files"] += 1

    return totals


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix hub-card and district-subnav links across all district pages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--root", required=True,
        help="Path to districts/ folder OR a single district subfolder",
    )
    parser.add_argument(
        "--write", action="store_true",
        help="Apply changes. Without this flag: dry run only.",
    )
    parser.add_argument(
        "--out-dir", default=None,
        help="Write fixed files here instead of in-place (optional)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print every individual link change",
    )
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    if not root_path.exists():
        sys.exit(f"Path not found: {root_path}")

    out_root = Path(args.out_dir).resolve() if args.out_dir else None

    print("=" * 62)
    print("  fix_district_links.py")
    if args.write:
        dest = f"WRITE → {out_root}" if out_root else "WRITE (in-place)"
    else:
        dest = "DRY RUN (no files will be changed)"
    print(f"  Mode   : {dest}")
    print(f"  Target : {root_path}")
    print("=" * 62)

    dry_log: list = []
    grand = {"subnav": 0, "hub": 0, "active": 0, "files": 0, "districts": 0}

    # ── Determine what to process ──
    # Case 1: root_path IS a single district folder (contains *.html but no
    #         districts/index.html slug list, and has no slug-named subdirs)
    # Case 2: root_path is the parent districts/ folder
    #
    # We distinguish by checking for the JS slug array in root/index.html.
    # If found, treat as parent. Otherwise check for subdirs with html.

    slugs_from_index = discover_slugs_from_index(root_path)

    if slugs_from_index is not None:
        # root_path is the districts/ parent
        district_dirs = discover_district_dirs(root_path)
    else:
        # Check for subdirs that contain html (another parent-dir signal)
        subdirs_with_html = sorted(
            d for d in root_path.iterdir()
            if d.is_dir() and list(d.glob("*.html"))
        )
        if subdirs_with_html:
            district_dirs = subdirs_with_html
            print(f"  ✓  Found {len(district_dirs)} district subfolder(s).")
        else:
            # Treat root_path itself as a single district folder
            district_dirs = [root_path]
            print("  ✓  Treating as single district folder.")

    for d in district_dirs:
        totals = process_district(d, args.write, out_root, args.verbose, dry_log)
        grand["subnav"]    += totals["subnav"]
        grand["hub"]       += totals["hub"]
        grand["active"]    += totals["active"]
        grand["files"]     += totals["files"]
        grand["districts"] += 1

    total_fixes = grand["subnav"] + grand["hub"] + grand["active"]

    print(f"\n{'='*62}")
    print("  SUMMARY")
    print(f"  Districts processed : {grand['districts']}")
    print(f"  HTML files examined : {grand['files']}")
    print(f"  Subnav link fixes   : {grand['subnav']}")
    print(f"  Hub-card fixes      : {grand['hub']}")
    print(f"  Active-tab fixes    : {grand['active']}")
    print(f"  {'─'*36}")
    print(f"  Total fixes         : {total_fixes}")

    if not args.write:
        print(f"\n  {len(dry_log)} file(s) would be modified.")
        print("  → Re-run with --write to apply changes.")
    else:
        print(f"\n  ✅ All done.")
    if out_root and args.write:
        print(f"  Output written to: {out_root}")
    print("=" * 62)


if __name__ == "__main__":
    main()