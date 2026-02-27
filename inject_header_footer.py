"""
inject_header_footer.py
-----------------------
Finds every HTML file in your NY districts directory that still has
the placeholder header/footer comments and replaces them with the
real NY Special Ed header and footer.

Targets these placeholder strings:
  <!-- standard NY header here -->
  <!-- standard NY footer here -->

SAFE TO RE-RUN — files that don't contain the placeholders are skipped.

USAGE:
  python inject_header_footer.py                          # all districts
  python inject_header_footer.py --district albany-city-sd  # one district
  python inject_header_footer.py --dry-run                # preview only
  python inject_header_footer.py --all-files              # hit every .html,
                                                          # not just partners
                                                          # and guide pages
"""

import argparse
import logging
from pathlib import Path

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

# Only inject into these filenames by default
# Use --all-files flag to hit every .html in district folders
TARGET_FILES = {
    "partners.html",
    "parent-advocacy-guide.html",
}

HEADER_PLACEHOLDER = "<!-- standard NY header here -->"
FOOTER_PLACEHOLDER = "<!-- standard NY footer here -->"

# ──────────────────────────────────────────────
#  REAL HEADER
# ──────────────────────────────────────────────
REAL_HEADER = """<header class="site-header" itemscope="" itemtype="http://schema.org/WPHeader">
<div class="nav-container">
<a href="/" class="nav-logo" aria-label="New York Special Ed - Home">
  <img src="/images/logo.png" alt="New York Special Ed logo" loading="eager" width="120" height="120" style="display:block; height:120px; width:auto; border-radius:8px;" />
</a>
<nav itemscope="" itemtype="http://schema.org/SiteNavigationElement" role="navigation">
<ul class="nav-links">
<li class="nav-item">
<a class="nav-link" href="/districts/">NYC Districts <i class="fas fa-chevron-down"></i></a>
<div class="mega-menu">
<div class="menu-column">
<h4>Manhattan (D1-6)</h4>
<ul>
<li><a href="/districts/nyc-district-01-lower-east-side">District 1: Lower East Side</a></li>
<li><a href="/districts/nyc-district-02-upper-east-side">District 2: Upper East Side/Tribeca</a></li>
<li><a href="/districts/nyc-district-03-upper-west-side">District 3: Upper West Side</a></li>
<li><a href="/districts/nyc-district-04-east-harlem">District 4: East Harlem</a></li>
<li><a href="/districts/nyc-district-05-central-harlem">District 5: Central Harlem</a></li>
<li><a href="/districts/nyc-district-06-washington-heights">District 6: Washington Heights</a></li>
</ul>
</div>
<div class="menu-column">
<h4>Brooklyn (Key Districts)</h4>
<ul>
<li><a href="/districts/nyc-district-15-park-slope">District 15: Park Slope/Sunset Park</a></li>
<li><a href="/districts/nyc-district-20-bay-ridge">District 20: Bay Ridge/Borough Park</a></li>
<li><a href="/districts/nyc-district-13-brooklyn-heights">District 13: Brooklyn Heights</a></li>
<li><a href="/districts/nyc-district-22-flatbush">District 22: Flatbush/Sheepshead</a></li>
<li><a href="/districts/nyc-district-75"><strong>District 75 (Citywide Programs)</strong></a></li>
</ul>
</div>
<div class="menu-column">
<h4>Queens &amp; SI</h4>
<ul>
<li><a href="/districts/nyc-district-24-corona">District 24: Corona/Maspeth</a></li>
<li><a href="/districts/nyc-district-26-bayside">District 26: Bayside</a></li>
<li><a href="/districts/nyc-district-30-astoria">District 30: Astoria/LIC</a></li>
<li><a href="/districts/nyc-district-31-staten-island">District 31: Staten Island</a></li>
<li><a href="/districts/" style="color: var(--ny-navy); font-weight: 700; margin-top: 10px;">View All 32 NYC Districts →</a></li>
</ul>
</div>
</div>
</li>
<li class="nav-item">
<a class="nav-link" href="/districts/nys-overview">Upstate &amp; LI <i class="fas fa-chevron-down"></i></a>
<div class="dropdown-menu">
<div class="menu-column" style="padding: 0 20px;">
<h4>Big 5 Cities</h4>
<ul>
<li><a href="/districts/buffalo-city-sd">Buffalo City SD</a></li>
<li><a href="/districts/rochester-city-sd">Rochester City SD</a></li>
<li><a href="/districts/syracuse-city-sd">Syracuse City SD</a></li>
<li><a href="/districts/yonkers-city-sd">Yonkers City SD</a></li>
<li><a href="/districts/albany-city-sd">Albany City SD</a></li>
</ul>
</div>
</div>
</li>
<li class="nav-item">
<a class="nav-link" href="/guides/">Parent Guides <i class="fas fa-chevron-down"></i></a>
<div class="dropdown-menu">
<div class="menu-column" style="padding: 0 20px;">
<ul>
<li><a href="/guides/cse-meeting-guide">CSE Meeting Guide</a></li>
<li><a href="/guides/evaluation-request-ny">Requesting an Evaluation</a></li>
<li><a href="/guides/bilingual-iep-new-york">Bilingual IEP Rights</a></li>
<li><a href="/guides/cpse-preschool-special-education">CPSE (Preschool) Guide</a></li>
<li><a href="/guides/carter-cases-private-placement">Private Placement (Carter Cases)</a></li>
</ul>
</div>
</div>
</li>
<li class="nav-item">
<a class="nav-link" href="/resources/">Free Tools</a>
</li>
<li class="nav-item">
<a class="nav-cta" href="/shop">Get The Toolkit</a>
</li>
</ul>
</nav>
<button aria-label="Open Navigation" class="mobile-toggle">
<i class="fas fa-bars"></i>
</button>
</div>
</header>"""

# ──────────────────────────────────────────────
#  REAL FOOTER
# ──────────────────────────────────────────────
REAL_FOOTER = """<footer class="site-footer" itemscope="" itemtype="http://schema.org/WPFooter">
<div class="footer-container">
<div class="footer-brand">
<h3>New York Special Ed<span>.net</span></h3>
<p>Demystifying the New York Committee on Special Education (CSE) process.
We provide parents with the localized data, legal templates, and advocacy
tools needed to secure appropriate services in NYC and NY State.</p>
<div style="margin-top: 20px;">
<a href="/shop" style="color: #D4AF37; font-weight: bold; text-decoration: none;">View Advocacy Shop →</a>
</div>
</div>
<div class="footer-col">
<h4>NY Parent Guides</h4>
<ul class="footer-links">
<li><a href="/guides/cse-meeting-guide">The CSE Meeting Guide</a></li>
<li><a href="/guides/evaluation-request-ny">Evaluation Timelines (60 Days)</a></li>
<li><a href="/guides/dispute-resolution-ny">Due Process &amp; Complaints</a></li>
<li><a href="/guides/bilingual-iep-new-york">Bilingual/ELL Rights</a></li>
<li><a href="/districts/nyc-district-75">District 75 Explained</a></li>
</ul>
</div>
<div class="footer-col">
<h4>Popular Districts</h4>
<ul class="footer-links">
<li><a href="/districts/nyc-district-02-upper-east-side">NYC District 2 (Manhattan)</a></li>
<li><a href="/districts/nyc-district-15-park-slope">NYC District 15 (Brooklyn)</a></li>
<li><a href="/districts/nyc-district-31-staten-island">NYC District 31 (Staten Island)</a></li>
<li><a href="/districts/nyc-district-30-astoria">NYC District 30 (Queens)</a></li>
<li><a href="/districts/buffalo-city-sd">Buffalo City Schools</a></li>
</ul>
</div>
<div class="footer-col">
<h4>Resources</h4>
<ul class="footer-links">
<li><a href="/about">About Us</a></li>
<li><a href="/contact">Contact Support</a></li>
<li><a href="/privacy-policy">Privacy Policy</a></li>
<li><a href="/terms">Terms of Service</a></li>
<li><a href="/sitemap.xml">Sitemap</a></li>
</ul>
</div>
</div>
<div class="footer-bottom">
<p>© 2026 NY Special Ed. Not legal advice. Not affiliated with the NYC DOE or NYSED.<br/>
For official inquiries, visit schools.nyc.gov or nysed.gov.</p>
</div>
</footer>"""

# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",   action="store_true", help="Preview only, no saves")
    parser.add_argument("--district",  type=str, default=None, help="Single district slug")
    parser.add_argument("--all-files", action="store_true", help="Process every .html file, not just partners/guide")
    args = parser.parse_args()

    districts_path = Path(DISTRICTS_DIR)
    if not districts_path.exists():
        log.error(f"Directory not found: {DISTRICTS_DIR}")
        return

    # Collect target folders
    folders = sorted([
        f for f in districts_path.iterdir()
        if f.is_dir()
        and f.name not in SKIP_FOLDERS
        and (args.district is None or f.name == args.district)
    ])

    log.info(f"Scanning {len(folders)} district folder(s)")
    if args.dry_run:
        log.info("DRY RUN — no files will be written")

    updated = skipped = 0

    for folder in folders:
        # Decide which files to process
        if args.all_files:
            html_files = list(folder.glob("*.html"))
        else:
            html_files = [
                folder / f for f in TARGET_FILES
                if (folder / f).exists()
            ]

        for filepath in html_files:
            content = filepath.read_text(encoding="utf-8", errors="replace")

            has_header_ph = HEADER_PLACEHOLDER in content
            has_footer_ph = FOOTER_PLACEHOLDER in content

            if not has_header_ph and not has_footer_ph:
                skipped += 1
                continue

            # Replace placeholders
            if has_header_ph:
                content = content.replace(HEADER_PLACEHOLDER, REAL_HEADER)
            if has_footer_ph:
                content = content.replace(FOOTER_PLACEHOLDER, REAL_FOOTER)

            if args.dry_run:
                log.info(f"  [DRY RUN] Would update: {filepath.relative_to(districts_path)}")
                log.info(f"    header: {'replaced' if has_header_ph else 'already present'}")
                log.info(f"    footer: {'replaced' if has_footer_ph else 'already present'}")
            else:
                filepath.write_text(content, encoding="utf-8")
                log.info(f"  ✓ {filepath.relative_to(districts_path)}")

            updated += 1

    log.info("─" * 50)
    log.info(f"Done.  Updated: {updated}  |  Already complete / skipped: {skipped}")


if __name__ == "__main__":
    main()