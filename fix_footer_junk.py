#!/usr/bin/env python3
"""
Fix the broken "Premium Newsletter Popup" comment that leaks visible text
(and a stray </body>) underneath the footer on every page.

What went wrong
---------------
Installation notes were pasted as an HTML comment that itself contained
another comment (<!-- nyse:extras:start -->). HTML comments can't nest, so the
first "-->" ended the outer comment early and the rest of the notes rendered
as visible text, plus a stray </body> tag in the middle of the page.

What this script does
---------------------
1. Replaces the broken opening comment (up to and including the
   <!-- nyse:extras:start --> marker) with just the marker.
2. Replaces the leaked "</body> on every page. ... ===== -->" text with a
   clean one-line comment. The extras, JS, and popup HTML are kept.
3. Writes a .bak backup next to every file it changes.
4. Preserves each file's original line endings and encoding.

Usage
-----
    python fix_footer_junk.py /path/to/site            # dry run (changes nothing)
    python fix_footer_junk.py /path/to/site --apply    # actually fix files
    python fix_footer_junk.py /path/to/site --apply --no-backup
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

# 1. Broken opening comment -> just the extras marker
OPENING = re.compile(
    r"<!--\s*=+\s*"                       # <!-- ==========
    r"NY Special Ed\s*[—–-]\s*Premium Newsletter Popup"
    r".*?"                                 # "Drop this just before ..."
    r"(<!--\s*nyse:extras:start\s*-->)",   # the first --> that closes it early
    re.DOTALL,
)

# 2. Leaked tail: "</body> on every page. ... ==== -->"
TAIL = re.compile(
    r"</body>\s*on every page\."
    r".*?"                                 # "Replaces the generic blue popup..." etc.
    r"=+\s*-->",
    re.DOTALL,
)


def fix_text(text: str):
    """Return (new_text, list_of_fixes_applied)."""
    fixes = []

    new, n = OPENING.subn(r"\1", text)
    if n:
        fixes.append("removed broken opening comment")
    text = new

    new, n = TAIL.subn("<!-- Newsletter popup -->", text)
    if n:
        fixes.append("removed leaked text + stray </body>")
    text = new

    return text, fixes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="site root folder")
    ap.add_argument("--apply", action="store_true", help="write changes (default is dry run)")
    ap.add_argument("--no-backup", action="store_true", help="don't write .bak files")
    ap.add_argument("--ext", nargs="+", default=[".html", ".htm"], help="file extensions to scan")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"Not a folder: {root}")

    scanned = changed = suspicious = 0

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in args.ext:
            continue
        scanned += 1

        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            print(f"SKIP (not utf-8): {path}")
            continue

        new_text, fixes = fix_text(text)

        if fixes:
            changed += 1
            print(f"{'FIXED' if args.apply else 'WOULD FIX'}: {path}  ({', '.join(fixes)})")
            if args.apply:
                if not args.no_backup:
                    shutil.copy2(path, str(path) + ".bak")
                path.write_bytes(new_text.encode("utf-8"))  # keeps \r\n as-is

        # Safety net: flag pages that still look wrong (e.g. a slightly different variant)
        remaining = new_text if args.apply else new_text
        if "Premium Newsletter Popup" in remaining or re.search(r"</body>\s*on every page", remaining):
            suspicious += 1
            print(f"  !! still looks broken, check by hand: {path}")
        elif remaining.lower().count("</body>") > 1:
            suspicious += 1
            print(f"  !! multiple </body> tags, check by hand: {path}")

    print(f"\nScanned {scanned} files, {'fixed' if args.apply else 'would fix'} {changed}, "
          f"{suspicious} need a manual look.")
    if not args.apply and changed:
        print("Dry run only. Re-run with --apply to write changes.")


if __name__ == "__main__":
    main()