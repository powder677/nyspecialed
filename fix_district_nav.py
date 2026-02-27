#!/usr/bin/env python3
"""
fix_district_nav.py
====================
Injects a consistent intra-district navigation strip into every HTML file
inside each district folder under districts/.

IDEMPOTENT — safe to run multiple times regardless of </head> whitespace style.
Old injections are replaced, not duplicated.

Usage
-----
  python fix_district_nav.py                           # auto-detects project root
  python fix_district_nav.py --root "C:\\path"         # explicit root
  python fix_district_nav.py --dry-run                 # preview changes, no writes
  python fix_district_nav.py --district buffalo-city-sd   # one district only

Requirements: Python 3.7+  (stdlib only — no pip installs needed)
"""

import argparse
import re
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# DISTRICT PAGE DEFINITIONS
# Order here = left-to-right order in the nav strip.
# Add / remove rows freely; pages that don't exist on disk are silently skipped.
# ──────────────────────────────────────────────────────────────────────────────
PAGE_DEFS = [
    ("index.html",                 "🏠", "Hub"),
    ("leadership-directory.html",  "📞", "Contacts"),
    ("cse-meeting-guide.html",     "🤝", "CSE Guide"),
    ("evaluation-process.html",    "📝", "Evaluations"),
    ("discipline-rights.html",     "⚖️",  "Discipline"),
    ("partners.html",              "🤲", "Partners"),
    ("special-ed-updates.html",    "📰", "Updates"),
]

# ──────────────────────────────────────────────────────────────────────────────
# CSS  (injected once per file into <head>)
# ──────────────────────────────────────────────────────────────────────────────
NAV_CSS = """\
<style>
/* district-subnav — auto-injected by fix_district_nav.py */
.district-subnav {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  margin: 0 0 24px 0;
}
.district-subnav a {
  display: inline-block;
  padding: 5px 11px;
  border-radius: 4px;
  font-size: 0.82rem;
  font-weight: 600;
  text-decoration: none;
  color: #0056b3;
  background: #fff;
  border: 1px solid #cbd5e1;
  white-space: nowrap;
  transition: background 0.15s;
}
.district-subnav a:hover { background: #dbeafe; }
.district-subnav a.subnav-active {
  background: #002868;
  color: #fff;
  border-color: #002868;
  cursor: default;
}
</style>"""

# Sentinel comments make injections idempotent (easy to find & replace)
CSS_START = "<!-- __district-subnav-css-start__ -->"
CSS_END   = "<!-- __district-subnav-css-end__ -->"
NAV_START = "<!-- __district-subnav-start__ -->"
NAV_END   = "<!-- __district-subnav-end__ -->"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def human_name(dir_name: str) -> str:
    """'buffalo-city-sd'  →  'Buffalo City SD'"""
    name = dir_name.replace("-", " ").title()
    for old, new in [(" Sd", " SD"), (" Nyc", " NYC"), (" Ny", " NY")]:
        name = name.replace(old, new)
    return name


def build_nav_html(existing_pages: set, current_file: str) -> str:
    links = []
    for fname, icon, label in PAGE_DEFS:
        if fname not in existing_pages:
            continue
        if fname == current_file:
            links.append(
                f'  <a href="./{fname}" class="subnav-active" aria-current="page">'
                f"{icon} {label}</a>"
            )
        else:
            links.append(f'  <a href="./{fname}">{icon} {label}</a>')
    return (
        '<nav class="district-subnav" aria-label="Pages in this district">\n'
        + "\n".join(links)
        + "\n</nav>"
    )


def strip_sentinel_block(text: str, start_marker: str, end_marker: str) -> str:
    """Remove an injected block including the \\n that immediately precedes the
    start marker.  This is the key to idempotency: strip then re-inject produces
    the identical bytes as the previous injection, regardless of </head> style.
    """
    pattern = re.compile(
        r"\n" + re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    return pattern.sub("", text)


def inject_css(text: str) -> str:
    """Insert the CSS sentinel block just before </head>.

    Strategy: we capture the optional \\n that precedes </head> and put it
    back *after* our block so the file structure is preserved exactly.
    That means strip_sentinel_block (which removes \\n + CSS_START…CSS_END)
    perfectly reverses this injection.

    Before:  ...title>\\n</head>   OR   ...title></head>
    After:   ...title>\\n<!-- css-start -->\\n<style>…\\n<!-- css-end -->\\n</head>
    """
    css_block = f"{CSS_START}\n{NAV_CSS}\n{CSS_END}"

    def replacer(m: re.Match) -> str:
        preceding_nl = m.group(1)   # '' or '\n'
        return f"\n{css_block}{preceding_nl}</head>"

    result, n = re.subn(r"(\n?)(</head>)", replacer, text, count=1)
    if n == 0:
        print("    ⚠  No </head> found — CSS not injected")
    return result


def inject_nav(text: str, nav_html: str) -> str:
    """Insert the nav sentinel block in the best location for this page type.

    Priority:
      1. Immediately after <div class="aeo-authority-block">…</div>  (sub-pages)
      2. After the closing </div> of <div class="hub-grid">          (index.html)
      3. Right after the opening <main …> tag                        (fallback)

    The block is prefixed with \\n so strip_sentinel_block reverses it cleanly.
    """
    nav_block = f"\n{NAV_START}\n{nav_html}\n{NAV_END}"

    # ── 1. aeo-authority-block ─────────────────────────────────────────────────
    aeo_re = re.compile(
        r'(<div\s+class="aeo-authority-block">.*?</div>)',
        re.DOTALL,
    )
    m = aeo_re.search(text)
    if m:
        return text[: m.end()] + nav_block + text[m.end() :]

    # ── 2. hub-grid (balance <div> tags to find correct closing </div>) ────────
    hub_open = text.find('<div class="hub-grid">')
    if hub_open != -1:
        depth, i = 0, hub_open
        while i < len(text):
            if text[i : i + 4] == "<div":
                depth += 1
                i += 4
            elif text[i : i + 6] == "</div>":
                depth -= 1
                if depth == 0:
                    end_pos = i + 6
                    return text[:end_pos] + nav_block + text[end_pos:]
                i += 6
            else:
                i += 1

    # ── 3. Opening <main …> tag ────────────────────────────────────────────────
    main_re = re.compile(r"(<main[^>]*>)")
    m = main_re.search(text)
    if m:
        return text[: m.end()] + nav_block + text[m.end() :]

    print("    ⚠  No suitable injection anchor found — page not modified")
    return text


def process_file(filepath: Path, existing_pages: set, dry_run: bool) -> bool:
    """Process one HTML file.  Returns True if the content changed."""
    try:
        original = filepath.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"    ✗ Read error: {exc}")
        return False

    text = original

    # Remove any previous injections
    text = strip_sentinel_block(text, CSS_START, CSS_END)
    text = strip_sentinel_block(text, NAV_START, NAV_END)

    # Re-inject fresh content
    text = inject_css(text)
    nav_html = build_nav_html(existing_pages, filepath.name)
    text = inject_nav(text, nav_html)

    changed = text != original
    if not dry_run and changed:
        filepath.write_text(text, encoding="utf-8")
    return changed


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Inject intra-district nav into all HTML files under districts/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        default=r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed",
        help="Project root directory (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files",
    )
    parser.add_argument(
        "--district",
        default=None,
        metavar="DIR_NAME",
        help="Process only one district, e.g.  buffalo-city-sd",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        root = Path.cwd()
        print(f"Specified root not found — falling back to CWD: {root}")

    districts_path = root / "districts"
    if not districts_path.exists():
        sys.exit(f"ERROR: {districts_path} does not exist.  Check --root.")

    if args.dry_run:
        print("── DRY RUN ── no files will be written\n")

    all_dirs = sorted(d for d in districts_path.iterdir() if d.is_dir())
    if args.district:
        all_dirs = [d for d in all_dirs if d.name == args.district]
        if not all_dirs:
            sys.exit(f"ERROR: district '{args.district}' not found under {districts_path}")

    known_filenames = {fname for fname, _, _ in PAGE_DEFS}
    total_files = total_changed = skipped_dirs = 0

    for district_dir in all_dirs:
        existing_pages = {
            fname for fname in known_filenames
            if (district_dir / fname).exists()
        }
        all_html = sorted(district_dir.glob("*.html"))

        if not all_html:
            skipped_dirs += 1
            continue

        label = human_name(district_dir.name)
        print(f"\n{'─' * 60}")
        print(f"  {label}  ({district_dir.name})")
        print(f"  Silo pages : {len(existing_pages)}/{len(known_filenames)}"
              f"  |  Total HTML: {len(all_html)}")
        print(f"{'─' * 60}")

        for html_file in all_html:
            changed = process_file(html_file, existing_pages, args.dry_run)
            if args.dry_run:
                status = "~ would update" if changed else "· no change  "
            else:
                status = "✓ updated     " if changed else "· no change  "
            print(f"  {status}  {html_file.name}")
            total_files += 1
            if changed:
                total_changed += 1

    verb = "would be " if args.dry_run else ""
    print(f"\n{'═' * 60}")
    print(f"  Districts processed : {len(all_dirs) - skipped_dirs}")
    print(f"  Districts skipped   : {skipped_dirs}  (no HTML files)")
    print(f"  Files processed     : {total_files}")
    print(f"  Files {verb}updated  : {total_changed}")
    print(f"  Files unchanged     : {total_files - total_changed}")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()