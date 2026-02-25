#!/usr/bin/env python3
"""
DIAGNOSTIC: Find every file containing ANY variation of the old domain.

Catches all variations like:
  - newyorkspecialed.net
  - newyorkspecialed.net
  - newyorkspecialed.net
  - newyorkspecialed.net  (with spaces)
  - new york special ed .com
  - newyorkspecialed.net
  ... and more

Usage:
    python find_old_domain.py                    (search only, safe)
    python find_old_domain.py --fix              (search + fix all)
    python find_old_domain.py --dir "C:\\path"   (custom project dir)
"""

import re
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_PROJECT_DIR = r"C:\Users\elisa\OneDrive\Documents\github\newyorkspecialed.net"

CORRECT_DOMAIN = "newyorkspecialed.net"

# ── All patterns to find ──────────────────────────────────────────────────────
# Each entry: (label, regex_pattern, replacement)
# replacement = None means "already correct, just flag it"
# All patterns use re.IGNORECASE

PATTERNS = [
    # ── Already correct (flag only, no replace) ───────────────────────────────
    (
        "ALREADY CORRECT",
        r"newyorkspecialed\.net",
        None,
    ),

    # ── newyorkspecialed.net and close variants ───────────────────────────────
    (
        "newyorkspecialed.net",
        r"newyorkspecialed\.com",
        CORRECT_DOMAIN,
    ),
    (
        "newyorkspecialed.net",
        r"new[\s\-_]*york[\s\-_]*special[\s\-_]*ed\.com",
        CORRECT_DOMAIN,
    ),
    (
        "newyorkspecialed.net",
        r"new[\s\-_]*york[\s\-_]*special[\s\-_]*education\.com",
        CORRECT_DOMAIN,
    ),

    # ── newyorkspecialed.net and close variants ────────────────────────────────────
    (
        "newyorkspecialed.net",
        r"newyorkspecialed.net\.com",
        CORRECT_DOMAIN,
    ),
    (
        "newyorkspecialed.net",
        r"ny[\s\-_]*special[\s\-_]*ed\.com",
        CORRECT_DOMAIN,
    ),
    (
        "newyorkspecialed.net (spaced)",
        r"ny\s+special\s+ed\s*\.com",
        CORRECT_DOMAIN,
    ),
    (
        "newyorkspecialed.net",
        r"ny[\s\-_]*special[\s\-_]*education\.com",
        CORRECT_DOMAIN,
    ),

    # ── Wrong .net short forms (newyorkspecialed.net instead of newyorkspecialed.net)
    # Matches newyorkspecialed.net but NOT newyorkspecialed.net
    (
        "newyorkspecialed.net (wrong short form)",
        r"\bnyspecialed\.net\b",
        CORRECT_DOMAIN,
    ),
    (
        "newyorkspecialed.net",
        r"ny[\s\-_]*special[\s\-_]*ed\.net",
        CORRECT_DOMAIN,
    ),
    (
        "newyorkspecialed.net",
        r"new[\s\-_]*york[\s\-_]*special[\s\-_]*ed\.net",
        CORRECT_DOMAIN,
    ),

    # ── Bare text mentions (no TLD) in display text / meta ───────────────────
    (
        "newyorkspecialed.net (bare, no TLD)",
        r"\bnyspecialed\b",
        CORRECT_DOMAIN,
    ),
]

# Directories to always skip
SKIP_DIRS = {
    ".git", "node_modules", ".next", "dist", "build",
    ".cache", "__pycache__", ".svelte-kit", ".vercel", ".netlify",
}

# Binary extensions to skip
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".mp3", ".wav", ".pdf", ".zip", ".gz", ".tar",
    ".exe", ".dll", ".so", ".pyc", ".map",
}

# ── Compile all patterns ──────────────────────────────────────────────────────

COMPILED = [
    (label, re.compile(pattern, re.IGNORECASE), replacement)
    for label, pattern, replacement in PATTERNS
]

# ── Core logic ────────────────────────────────────────────────────────────────

def search_all_files(project_dir: str, fix: bool = False):
    root = Path(project_dir)
    if not root.exists():
        print(f"[ERROR] Directory not found: {project_dir}")
        return

    found_files   = []
    correct_files = []
    skipped_count = 0
    total_hits    = 0

    print(f"\nScanning : {root}")
    print(f"Fix mode : {'YES - will replace' if fix else 'NO  - preview only'}")
    print(f"Patterns : {len(PATTERNS)} variations\n")
    print("=" * 70)

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix.lower() in BINARY_EXTENSIONS:
            skipped_count += 1
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            skipped_count += 1
            continue

        rel = path.relative_to(root)

        file_hits  = []   # (label, line_num, highlighted_line)
        already_ok = []   # (line_num, highlighted_line)

        # Track which lines already matched to avoid duplicate reporting
        matched_lines = set()

        for label, compiled, replacement in COMPILED:
            for line_num, line in enumerate(content.splitlines(), start=1):
                if not compiled.search(line):
                    continue
                # Skip if this line was already flagged as correct
                if replacement is None and line_num in matched_lines:
                    continue

                display = line.strip()
                if len(display) > 120:
                    display = display[:117] + "..."
                highlighted = compiled.sub(f">>>>{label}<<<<", display)

                if replacement is None:
                    already_ok.append((line_num, highlighted))
                else:
                    if line_num not in matched_lines:
                        file_hits.append((label, line_num, highlighted))
                        matched_lines.add(line_num)

        if not file_hits and not already_ok:
            continue

        # ── Report this file ──────────────────────────────────────────────────
        print(f"\n  FILE: {rel}  [{path.suffix or 'no ext'}]")

        if already_ok:
            correct_files.append(rel)
            for line_num, highlighted in already_ok:
                print(f"   [OK]  Line {line_num:>5}: {highlighted}")

        if file_hits:
            found_files.append(rel)
            total_hits += len(file_hits)
            for label, line_num, highlighted in file_hits:
                print(f"   [!!]  Line {line_num:>5} [{label}]: {highlighted}")

            if fix:
                fixed_content = content
                fix_count = 0
                for label, compiled, replacement in COMPILED:
                    if replacement is None:
                        continue
                    fixed_content, n = compiled.subn(replacement, fixed_content)
                    fix_count += n
                path.write_text(fixed_content, encoding="utf-8")
                print(f"   --> FIXED {fix_count} occurrence(s) -> {CORRECT_DOMAIN}")

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"\nSUMMARY")
    print(f"  Files needing fixes    : {len(found_files)}")
    print(f"  Total bad occurrences  : {total_hits}")
    print(f"  Already correct files  : {len(correct_files)}")
    print(f"  Skipped (binary/err)   : {skipped_count}")

    if found_files:
        print(f"\n  Files with issues:")
        for f in found_files:
            print(f"    [!!] {f}")
        if not fix:
            print(f"\n  Run with --fix to automatically replace everything:")
            print(f"  python find_old_domain.py --fix")
        else:
            print(f"\n  All occurrences replaced with: {CORRECT_DOMAIN}")
    else:
        print(f"\n  No bad domain references found!")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Find and fix ALL domain name variations across your project."
    )
    parser.add_argument(
        "--dir",
        default=DEFAULT_PROJECT_DIR,
        help="Path to project root (default: %(default)s)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help=f"Replace all bad domains with '{CORRECT_DOMAIN}'",
    )
    args = parser.parse_args()
    search_all_files(args.dir, fix=args.fix)


if __name__ == "__main__":
    main()