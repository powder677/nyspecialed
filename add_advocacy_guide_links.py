"""
add_advocacy_guide_links.py
----------------------------
Two things per district folder:

TASK 1 — index.html
  Adds a new hub card for parent-advocacy-guide.html into the
  .hub-grid section, after the existing partners card.
  Only runs if parent-advocacy-guide.html exists in the folder
  and the card isn't already there.

TASK 2 — all silo pages
  Adds parent-advocacy-guide.html to the silo nav / district
  subnav on every existing district page that has a nav block.
  Targets both nav patterns used in the NY site:
    - .silo-nav  (new partners/guide pages)
    - .district-subnav  (older pages like cse-meeting-guide.html)
  Only adds the link if it isn't already present.

SILO PAGES TARGETED:
  index.html, cse-meeting-guide.html, evaluation-process.html,
  discipline-rights.html, leadership-directory.html,
  special-ed-updates.html, partners.html

USAGE:
  python add_advocacy_guide_links.py                           # all districts
  python add_advocacy_guide_links.py --district albany-city-sd # one district
  python add_advocacy_guide_links.py --dry-run                 # preview only
  python add_advocacy_guide_links.py --no-skip                 # reprocess all
"""

import argparse
import logging
import re
from pathlib import Path
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
DISTRICTS_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\districts"

SKIP_FOLDERS = {
    "about", "contact", "resources", "blog", "images",
    "styles", "css", "js", "assets", "guides", "shop",
    "privacy-policy", "terms", "sitemap", "advertise",
    "nys-overview",
}

SILO_FILES = [
    "index.html",
    "cse-meeting-guide.html",
    "evaluation-process.html",
    "discipline-rights.html",
    "leadership-directory.html",
    "special-ed-updates.html",
    "partners.html",
]

# Marker written into index.html so we don't double-add the card
INDEX_MARKER = "<!-- advocacy-guide-card-added -->"

# ──────────────────────────────────────────────
#  TASK 1 — Hub card HTML for index.html
# ──────────────────────────────────────────────
def make_hub_card() -> str:
    return """<!-- advocacy-guide-card-added -->
<a class="hub-card" href="parent-advocacy-guide.html">
<h3 style="color: #0056b3; margin-top: 0;">📋 Advocacy Guide</h3>
<p>CSE pitfalls, parent rights, IEP strategies, and FAQ.</p>
</a>"""


def inject_index_card(html: str) -> tuple[str, bool]:
    """
    Insert the advocacy guide hub card into the .hub-grid.
    Returns (updated_html, was_changed).
    Strategy: find the last existing hub-card and insert after it.
    """
    if INDEX_MARKER in html:
        return html, False  # already done

    # Find the last </a> that closes a hub-card inside hub-grid
    # We look for the closing </a> of the partners card or the last card
    # Use a simple string approach — BeautifulSoup restructures the grid oddly
    
    # Pattern: find the hub-grid div and insert before its closing </div>
    # First try to insert after the partners card specifically
    partners_card_pattern = re.compile(
        r'(href=["\']partners\.html["\'][^>]*>.*?</a>)',
        re.DOTALL | re.IGNORECASE
    )
    match = partners_card_pattern.search(html)
    
    if match:
        insert_pos = match.end()
        new_html = html[:insert_pos] + "\n" + make_hub_card() + html[insert_pos:]
        return new_html, True

    # Fallback: find hub-grid closing div and insert before it
    grid_close = html.rfind('</div>', html.find('class="hub-grid"'))
    if grid_close != -1:
        new_html = html[:grid_close] + "\n" + make_hub_card() + "\n" + html[grid_close:]
        return new_html, True

    return html, False


# ──────────────────────────────────────────────
#  TASK 2 — Silo nav link injection
# ──────────────────────────────────────────────
GUIDE_LINK_TEXT  = "Advocacy Guide"
GUIDE_FILENAME   = "parent-advocacy-guide.html"

def has_guide_link(html: str) -> bool:
    return GUIDE_FILENAME in html


def inject_silo_nav_link(html: str, filename: str) -> tuple[str, bool]:
    """
    Add advocacy guide link to whatever nav pattern this page uses.
    Returns (updated_html, was_changed).
    """
    if has_guide_link(html):
        return html, False

    soup = BeautifulSoup(html, "lxml")
    changed = False

    # ── Pattern A: .silo-nav (new partners / guide pages) ──────────
    silo_nav = soup.find("nav", class_="silo-nav")
    if silo_nav:
        # Find the partners.html link and insert after it,
        # or just append to the nav if partners link not found
        partners_link = silo_nav.find("a", href="partners.html")
        new_tag = soup.new_tag("a", href=GUIDE_FILENAME)
        new_tag.string = GUIDE_LINK_TEXT

        if partners_link:
            partners_link.insert_after(new_tag)
        else:
            # Append to end of nav
            silo_nav.append(new_tag)
        changed = True

    # ── Pattern B: .district-subnav (older pages) ──────────────────
    subnav = soup.find("nav", class_="district-subnav")
    if not subnav:
        # Some older pages use a div instead of nav
        subnav = soup.find("div", class_="district-subnav")

    if subnav and not changed:
        partners_link = subnav.find("a", href="partners.html")
        if not partners_link:
            partners_link = subnav.find("a", string=re.compile("partners", re.I))

        new_tag = soup.new_tag("a", href=GUIDE_FILENAME)
        new_tag.string = GUIDE_LINK_TEXT

        if partners_link:
            partners_link.insert_after(new_tag)
        else:
            subnav.append(new_tag)
        changed = True

    # ── Pattern C: inline silo nav in older pages ──────────────────
    # Some pages have silo nav as a plain div with class "silo-nav"
    if not changed:
        silo_div = soup.find("div", class_="silo-nav")
        if silo_div:
            partners_link = silo_div.find("a", href="partners.html")
            new_tag = soup.new_tag("a", href=GUIDE_FILENAME)
            new_tag.string = GUIDE_LINK_TEXT

            if partners_link:
                partners_link.insert_after(new_tag)
            else:
                silo_div.append(new_tag)
            changed = True

    if changed:
        return str(soup), True
    return html, False


# ──────────────────────────────────────────────
#  PROCESS ONE DISTRICT
# ──────────────────────────────────────────────
def process_district(folder: Path, args) -> dict:
    slug = folder.name
    guide_file = folder / GUIDE_FILENAME
    results = {"index": False, "silo": 0}

    # Only process if the advocacy guide page actually exists
    if not guide_file.exists():
        log.debug(f"  SKIP {slug} — no parent-advocacy-guide.html yet")
        return results

    log.info(f"── {slug} ──────────────────────────────────")

    # ── TASK 1: index.html card ────────────────────────────────────
    index_file = folder / "index.html"
    if index_file.exists():
        html = index_file.read_text(encoding="utf-8", errors="replace")
        if not args.no_skip and INDEX_MARKER in html:
            log.info("  index.html   SKIP — card already present")
        else:
            updated, changed = inject_index_card(html)
            if changed:
                if args.dry_run:
                    log.info("  index.html   [DRY RUN] would add hub card")
                else:
                    index_file.write_text(updated, encoding="utf-8")
                    log.info("  index.html   ✓ hub card added")
                results["index"] = True
            else:
                log.info("  index.html   SKIP — could not find insertion point")
    else:
        log.warning(f"  index.html   NOT FOUND in {slug}")

    # ── TASK 2: silo page nav links ────────────────────────────────
    for filename in SILO_FILES:
        if filename == "index.html":
            continue  # handled above separately

        filepath = folder / filename
        if not filepath.exists():
            continue

        html = filepath.read_text(encoding="utf-8", errors="replace")

        if not args.no_skip and has_guide_link(html):
            log.info(f"  {filename:<35} SKIP — link already present")
            continue

        updated, changed = inject_silo_nav_link(html, filename)
        if changed:
            if args.dry_run:
                log.info(f"  {filename:<35} [DRY RUN] would add nav link")
            else:
                filepath.write_text(updated, encoding="utf-8")
                log.info(f"  {filename:<35} ✓ nav link added")
            results["silo"] += 1
        else:
            log.warning(f"  {filename:<35} ⚠ no nav pattern found — skipped")

    return results


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",   action="store_true", help="Preview only, no saves")
    parser.add_argument("--district",  type=str, default=None, help="Single district slug")
    parser.add_argument("--no-skip",   action="store_true", help="Reprocess already-done files")
    args = parser.parse_args()

    districts_path = Path(DISTRICTS_DIR)
    if not districts_path.exists():
        log.error(f"Directory not found: {DISTRICTS_DIR}")
        return

    folders = sorted([
        f for f in districts_path.iterdir()
        if f.is_dir()
        and f.name not in SKIP_FOLDERS
        and (args.district is None or f.name == args.district)
    ])

    log.info(f"Districts to process: {len(folders)}")
    if args.dry_run:
        log.info("DRY RUN — no files will be written")

    total_index = 0
    total_silo  = 0
    no_guide    = 0

    for folder in folders:
        try:
            r = process_district(folder, args)
            if r["index"]:
                total_index += 1
            total_silo += r["silo"]
            if not (folder / GUIDE_FILENAME).exists():
                no_guide += 1
        except Exception as e:
            log.error(f"  ERROR {folder.name}: {e}")

    log.info("═" * 55)
    log.info(f"index.html cards added : {total_index}")
    log.info(f"silo nav links added   : {total_silo}")
    log.info(f"skipped (no guide yet) : {no_guide}")


if __name__ == "__main__":
    main()