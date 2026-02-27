"""
fix_ny_404s_v2.py
─────────────────────────────────────────────────────────
Fixes all 12 404s from the Feb 27 2026 (13:52) audit.

ISSUE BREAKDOWN:

  FIX 1 — ../parent-advocacy-guide.html bad relative link
    20 inlinks from D01 pages pointing up a level to
    /districts/parent-advocacy-guide.html instead of staying
    in /districts/nyc-district-01-lower-east-side/

  FIX 2 — /about/mission and /about/methodology missing .html
    The about pages link to extensionless versions of themselves
    (probably in their own canonical tag or nav).
    Find and add .html to those hrefs.

  FIX 3 — Shortened silo nav hrefs in new districts
    Vertex generated cse.html / eval.html / disc.html
    instead of the real filenames. Affects all pages in:
      sachem-csd, east-ramapo-csd, greece-csd

USAGE:
  python fix_ny_404s_v2.py            # run all fixes
  python fix_ny_404s_v2.py --dry-run  # preview only
"""

import re
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────
SITE_ROOT     = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
DISTRICTS_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\districts"

# New districts whose silo navs have shortened hrefs
NEW_DISTRICT_SLUGS = [
    "sachem-csd",
    "east-ramapo-csd",
    "greece-csd",
    "patchogue-medford-ufsd",  # include in case same issue
]

# Vertex-generated short hrefs → correct full filenames
SHORT_HREF_MAP = {
    '"cse.html"':  '"cse-meeting-guide.html"',
    "'cse.html'":  "'cse-meeting-guide.html'",
    '"eval.html"': '"evaluation-process.html"',
    "'eval.html'": "'evaluation-process.html'",
    '"disc.html"': '"discipline-rights.html"',
    "'disc.html'": "'discipline-rights.html'",
    # also catch without quotes in case Vertex dropped them
    'href=cse.html':  'href=cse-meeting-guide.html',
    'href=eval.html': 'href=evaluation-process.html',
    'href=disc.html': 'href=discipline-rights.html',
}

# ── Helpers ───────────────────────────────────────────────────

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def write(path: Path, text: str, dry_run: bool, label: str):
    if dry_run:
        log.info(f"  [DRY RUN] would write: {label}")
    else:
        path.write_text(text, encoding="utf-8")
        log.info(f"  ✓ {label}")


# ── FIX 1: ../parent-advocacy-guide.html in D01 ───────────────
def fix_1_d01_guide_link(dry_run: bool):
    log.info("FIX 1 ── ../parent-advocacy-guide.html bad relative link in D01")
    d01 = Path(DISTRICTS_DIR) / "nyc-district-01-lower-east-side"

    if not d01.exists():
        log.warning(f"  Folder not found: {d01}")
        return

    fixed = 0
    for f in sorted(d01.rglob("*.html")):
        text = read(f)
        if "../parent-advocacy-guide.html" not in text:
            continue
        new_text = text.replace("../parent-advocacy-guide.html",
                                "parent-advocacy-guide.html")
        count = text.count("../parent-advocacy-guide.html")
        write(f, new_text, dry_run, f"{f.name} ({count} link{'s' if count>1 else ''})")
        fixed += count

    if fixed == 0:
        log.info("  Nothing to fix — link may already be correct")
    else:
        log.info(f"  Total: {fixed} bad link(s) corrected in D01")


# ── FIX 2: /about/mission and /about/methodology missing .html ─
def fix_2_about_extensionless(dry_run: bool):
    log.info("FIX 2 ── Adding .html to extensionless /about hrefs")
    about_dir = Path(SITE_ROOT) / "about"

    if not about_dir.exists():
        log.warning(f"  /about directory not found: {about_dir}")
        return

    # Patterns that produce extensionless self-links
    # e.g. href="/about/mission"  href="mission"  canonical="/about/mission"
    replacements = [
        # canonical tags and hrefs pointing to extensionless paths
        (r'(href=["\'](?:https://www\.newyorkspecialed\.net)?/about/mission)["\']',
         r'\1.html"'),
        (r'(href=["\'](?:https://www\.newyorkspecialed\.net)?/about/methodology)["\']',
         r'\1.html"'),
        (r'(content=["\'](?:https://www\.newyorkspecialed\.net)?/about/mission)["\']',
         r'\1.html"'),
        (r'(content=["\'](?:https://www\.newyorkspecialed\.net)?/about/methodology)["\']',
         r'\1.html"'),
    ]

    # Check every HTML file in /about
    fixed = 0
    for f in sorted(about_dir.rglob("*.html")):
        text = read(f)
        new_text = text
        file_fixes = 0

        for pattern, replacement in replacements:
            matches = re.findall(pattern, new_text, re.IGNORECASE)
            if matches:
                new_text = re.sub(pattern, replacement, new_text, flags=re.IGNORECASE)
                file_fixes += len(matches)

        if file_fixes:
            write(f, new_text, dry_run, f"about/{f.name} ({file_fixes} fix{'es' if file_fixes>1 else ''})")
            fixed += file_fixes

    # Also check site-wide for nav links to /about/mission and /about/methodology
    # (in case the main nav or footer has them)
    site_root = Path(SITE_ROOT)
    for f in site_root.rglob("*.html"):
        if "about" in str(f):
            continue  # already handled above
        text = read(f)
        new_text = text
        file_fixes = 0

        for pattern, replacement in replacements:
            matches = re.findall(pattern, new_text, re.IGNORECASE)
            if matches:
                new_text = re.sub(pattern, replacement, new_text, flags=re.IGNORECASE)
                file_fixes += len(matches)

        if file_fixes:
            rel = f.relative_to(site_root)
            write(f, new_text, dry_run, f"{rel} ({file_fixes} fix{'es' if file_fixes>1 else ''})")
            fixed += file_fixes

    if fixed == 0:
        log.info("  Nothing found — links may already have .html or use a different format")
        log.info("  TIP: manually check <link rel='canonical'> in mission.html and methodology.html")
    else:
        log.info(f"  Total: {fixed} extensionless href(s) corrected")


# ── FIX 3: Shortened silo nav hrefs in new districts ──────────
def fix_3_short_hrefs(dry_run: bool):
    log.info("FIX 3 ── Replacing cse.html / eval.html / disc.html in new district pages")
    districts_path = Path(DISTRICTS_DIR)
    total_fixes = 0
    total_files = 0

    for slug in NEW_DISTRICT_SLUGS:
        folder = districts_path / slug
        if not folder.exists():
            log.info(f"  SKIP {slug} — folder not found")
            continue

        slug_fixes = 0
        for f in sorted(folder.rglob("*.html")):
            text = read(f)
            new_text = text
            file_fixes = 0

            for bad, good in SHORT_HREF_MAP.items():
                if bad in new_text:
                    count = new_text.count(bad)
                    new_text = new_text.replace(bad, good)
                    file_fixes += count

            if file_fixes:
                write(f, new_text, dry_run,
                      f"{slug}/{f.name} ({file_fixes} href{'s' if file_fixes>1 else ''})")
                slug_fixes += file_fixes
                total_files += 1

        if slug_fixes:
            log.info(f"  {slug}: {slug_fixes} href(s) corrected")
            total_fixes += slug_fixes
        else:
            log.info(f"  {slug}: nothing to fix")

    if total_fixes == 0:
        log.info("  No shortened hrefs found in any new district folder")
    else:
        log.info(f"  Total: {total_fixes} href(s) fixed across {total_files} file(s)")


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fix 404s from Feb 27 13:52 audit")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    args = parser.parse_args()

    log.info("═" * 60)
    log.info("NY Special Ed — 404 Fix Script v2")
    log.info(f"Site root: {SITE_ROOT}")
    if args.dry_run:
        log.info("DRY RUN — no files will be written")
    log.info("═" * 60)

    fix_1_d01_guide_link(args.dry_run)
    log.info("")
    fix_2_about_extensionless(args.dry_run)
    log.info("")
    fix_3_short_hrefs(args.dry_run)

    log.info("")
    log.info("═" * 60)
    log.info("Done. Next steps:")
    log.info("  1. Deploy changes")
    log.info("  2. Submit fixed URLs in Google Search Console → URL Inspection → Request Indexing")
    log.info("  3. Re-crawl with Ahrefs in 24h to confirm 0 remaining 404s")


if __name__ == "__main__":
    main()