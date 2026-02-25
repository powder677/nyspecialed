#!/usr/bin/env python3
"""
Fixes two problems across the project:

  1. NAVBAR LOGO: Any <a> or <img> tag referencing nyspecialed.com (or variants)
     where the logo should be gets corrected to use /logo.png with proper HTML.

  2. GIT MERGE CONFLICTS: Removes <<<<<<< HEAD / ======= / >>>>>>> markers
     and keeps only the TOP section (HEAD = your local version) of each conflict.

Usage:
    python fix_navbar_and_conflicts.py              (preview, no changes)
    python fix_navbar_and_conflicts.py --fix        (apply all fixes)
    python fix_navbar_and_conflicts.py --dir "C:\\path"
    python fix_navbar_and_conflicts.py --fix --conflicts-keep bottom
                                                    (keep incoming instead of HEAD)
"""

import re
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_PROJECT_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"

# What the corrected logo anchor should look like.
# Adjust the class names to match your project's CSS.
LOGO_REPLACEMENT = '<a href="/"><img src="/logo.png" alt="New York Special Ed" class="site-logo" /></a>'

# File extensions to scan
TEXT_EXTENSIONS = {
    ".html", ".htm", ".jsx", ".tsx", ".astro", ".svelte",
    ".vue", ".njk", ".liquid", ".md", ".js", ".ts",
}

SKIP_DIRS = {
    ".git", "node_modules", ".next", "dist", "build",
    ".cache", "__pycache__", ".svelte-kit", ".vercel", ".netlify",
}

# ── Regex patterns ────────────────────────────────────────────────────────────

# Matches any anchor or img tag that contains a bad domain near "logo"
# Catches things like:
#   <a href="https://nyspecialed.com"><img src="logo.png" ...>
#   <img src="https://nyspecialed.com/logo.png" ...>
#   <a href="nyspecialed.com" class="logo">
LOGO_LINK_PATTERN = re.compile(
    r'<a[^>]*(?:nyspecialed|ny[\s\-_]*special[\s\-_]*ed)[^>]*>.*?</a>'
    r'|<img[^>]*(?:nyspecialed|ny[\s\-_]*special[\s\-_]*ed)[^>]*/?>',
    re.IGNORECASE | re.DOTALL,
)

# Git conflict markers
# Captures: <<<<<<< HEAD ... ======= ... >>>>>>> branch-name
CONFLICT_PATTERN = re.compile(
    r'<{7}.*?\n(.*?)\n={7}\n(.*?)\n>{7}[^\n]*',
    re.DOTALL,
)


# ── Fix functions ─────────────────────────────────────────────────────────────

def fix_logo_links(content: str) -> tuple[str, int]:
    """Replace bad logo anchor/img tags with the correct logo HTML."""
    new_content, count = LOGO_LINK_PATTERN.subn(LOGO_REPLACEMENT, content)
    return new_content, count


def fix_conflict_markers(content: str, keep: str = "top") -> tuple[str, int]:
    """
    Remove git merge conflict markers.
    keep='top'    → keep HEAD (your local changes)
    keep='bottom' → keep incoming (the other branch)
    """
    count = len(CONFLICT_PATTERN.findall(content))
    if keep == "top":
        new_content = CONFLICT_PATTERN.sub(lambda m: m.group(1), content)
    else:
        new_content = CONFLICT_PATTERN.sub(lambda m: m.group(2), content)
    return new_content, count


def has_conflict_markers(content: str) -> bool:
    return bool(re.search(r'^<{7} |^={7}$|^>{7} ', content, re.MULTILINE))


# ── Main scanner ──────────────────────────────────────────────────────────────

def scan_and_fix(project_dir: str, fix: bool = False, keep: str = "top"):
    root = Path(project_dir)
    if not root.exists():
        print(f"[ERROR] Directory not found: {project_dir}")
        return

    logo_files     = []
    conflict_files = []
    both_files     = []
    skipped        = 0

    print(f"\nScanning : {root}")
    print(f"Fix mode : {'YES - will apply changes' if fix else 'NO  - preview only'}")
    print(f"Conflicts: keeping {'HEAD (top/local)' if keep == 'top' else 'incoming (bottom)'} side")
    print("=" * 70)

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            skipped += 1
            continue

        rel          = path.relative_to(root)
        has_logo     = bool(LOGO_LINK_PATTERN.search(content))
        has_conflict = has_conflict_markers(content)

        if not has_logo and not has_conflict:
            continue

        print(f"\n  FILE: {rel}")

        # ── Logo issues ───────────────────────────────────────────────────────
        if has_logo:
            matches = LOGO_LINK_PATTERN.findall(content)
            logo_files.append(rel)
            for m in matches:
                snippet = m.strip()[:100] + ("..." if len(m) > 100 else "")
                print(f"   [LOGO]  Found bad logo tag:")
                print(f"           {snippet}")
                print(f"           --> {LOGO_REPLACEMENT}")

        # ── Conflict markers ──────────────────────────────────────────────────
        if has_conflict:
            conflict_files.append(rel)
            conflicts = CONFLICT_PATTERN.findall(content)
            print(f"   [CONFLICT] {len(conflicts)} merge conflict(s) found")
            for i, (head_side, incoming_side) in enumerate(conflicts, 1):
                h = head_side.strip()[:80] + ("..." if len(head_side.strip()) > 80 else "")
                b = incoming_side.strip()[:80] + ("..." if len(incoming_side.strip()) > 80 else "")
                print(f"     Conflict #{i}:")
                print(f"       HEAD     : {h}")
                print(f"       Incoming : {b}")
                print(f"       Keeping  : {'HEAD' if keep == 'top' else 'Incoming'}")

        if has_logo and has_conflict:
            both_files.append(rel)

        # ── Apply fixes ───────────────────────────────────────────────────────
        if fix:
            updated = content
            if has_logo:
                updated, n = fix_logo_links(updated)
                print(f"   --> Fixed {n} logo tag(s)")
            if has_conflict:
                updated, n = fix_conflict_markers(updated, keep=keep)
                print(f"   --> Resolved {n} merge conflict(s)")
            path.write_text(updated, encoding="utf-8")
            print(f"   --> Saved")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"\nSUMMARY")
    print(f"  Files with bad logo tags    : {len(logo_files)}")
    print(f"  Files with conflict markers : {len(conflict_files)}")
    print(f"  Files with BOTH issues      : {len(both_files)}")
    print(f"  Skipped                     : {skipped}")

    all_affected = sorted(set(logo_files) | set(conflict_files))
    if all_affected:
        print(f"\n  All affected files:")
        for f in all_affected:
            tags = []
            if f in logo_files:     tags.append("LOGO")
            if f in conflict_files: tags.append("CONFLICT")
            print(f"    [{'+'.join(tags)}] {f}")

        if not fix:
            print(f"\n  Run with --fix to apply all changes:")
            print(f"  python fix_navbar_and_conflicts.py --fix")
    else:
        print("\n  No issues found!")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fix navbar logo links and git merge conflict markers."
    )
    parser.add_argument(
        "--dir", default=DEFAULT_PROJECT_DIR,
        help="Path to project root",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply all fixes (default is preview only)",
    )
    parser.add_argument(
        "--conflicts-keep", choices=["top", "bottom"], default="top",
        dest="keep",
        help="Which side of merge conflicts to keep: 'top' = HEAD/yours (default), 'bottom' = incoming",
    )
    args = parser.parse_args()
    scan_and_fix(args.dir, fix=args.fix, keep=args.keep)


if __name__ == "__main__":
    main()