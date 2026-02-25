#!/usr/bin/env python3
"""
DIAGNOSTIC: Find every file containing newyorkspecialed.net
Shows the file path, file type, and the exact lines where it appears.

Usage:
    python find_old_domain.py
    python find_old_domain.py --fix      (fix after reviewing)
    python find_old_domain.py --dir "C:\\path\\to\\project"
"""

import os
import re
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_PROJECT_DIR = r"C:\Users\elisa\OneDrive\Documents\github\newyorkspecialed.net"

OLD_DOMAIN = "newyorkspecialed.net"
NEW_DOMAIN = "newyorkspecialed.net"

# Directories to always skip
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", ".cache", "__pycache__", ".svelte-kit"}

# Binary file extensions to skip (can't contain readable domain text)
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".mp3", ".wav", ".pdf", ".zip", ".gz", ".tar",
    ".exe", ".dll", ".so", ".pyc",
}

# ── Core logic ────────────────────────────────────────────────────────────────

def search_all_files(project_dir: str, fix: bool = False):
    root = Path(project_dir)
    if not root.exists():
        print(f"[ERROR] Directory not found: {project_dir}")
        return

    pattern = re.compile(re.escape(OLD_DOMAIN), re.IGNORECASE)
    
    found_files = []
    skipped_binary = 0
    skipped_unreadable = 0

    print(f"\nScanning: {root}")
    print(f"Looking for: '{OLD_DOMAIN}'\n")
    print("=" * 70)

    for path in sorted(root.rglob("*")):
        # Skip directories
        if not path.is_file():
            continue

        # Skip unwanted dirs
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue

        # Skip binary file types
        if path.suffix.lower() in BINARY_EXTENSIONS:
            skipped_binary += 1
            continue

        # Try to read the file
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            skipped_unreadable += 1
            continue

        # Search for old domain
        matches = []
        for line_num, line in enumerate(content.splitlines(), start=1):
            if pattern.search(line):
                matches.append((line_num, line.strip()))

        if not matches:
            continue

        # Report findings
        rel = path.relative_to(root)
        found_files.append(path)
        print(f"\n📄 FILE: {rel}  [{path.suffix or 'no extension'}]")
        print(f"   Occurrences: {len(matches)}")
        for line_num, line in matches:
            # Truncate very long lines
            display = line if len(line) <= 120 else line[:117] + "..."
            # Highlight the match
            highlighted = pattern.sub(f">>>>{OLD_DOMAIN}<<<<", display)
            print(f"   Line {line_num:>5}: {highlighted}")

        # Optionally fix in place
        if fix:
            fixed_content, count = pattern.subn(NEW_DOMAIN, content)
            path.write_text(fixed_content, encoding="utf-8")
            print(f"   ✅ FIXED {count} occurrence(s)")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"\n📊 SUMMARY")
    print(f"   Files WITH old domain : {len(found_files)}")
    print(f"   Binary files skipped  : {skipped_binary}")
    print(f"   Unreadable files skipped: {skipped_unreadable}")

    if found_files:
        print(f"\n   Files to fix:")
        for f in found_files:
            print(f"     • {f.relative_to(root)}")

        if not fix:
            print(f"\n👉 Run with --fix to automatically replace all occurrences.")
        else:
            print(f"\n✅ All occurrences have been fixed.")
    else:
        print("\n   ✅ No occurrences of the old domain found.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=f"Find (and optionally fix) all '{OLD_DOMAIN}' references in your project."
    )
    parser.add_argument(
        "--dir",
        default=DEFAULT_PROJECT_DIR,
        help="Path to project root (default: %(default)s)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help=f"Replace '{OLD_DOMAIN}' with '{NEW_DOMAIN}' in every file found.",
    )
    args = parser.parse_args()

    search_all_files(args.dir, fix=args.fix)


if __name__ == "__main__":
    main()