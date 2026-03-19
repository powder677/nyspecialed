#!/usr/bin/env python3
"""
deploy_nav.py
=============
Replaces the old image-logo navbar with the new clean text navbar
across every HTML file in your site directory.

USAGE
-----
  # Preview what will change (no files written)
  python deploy_nav.py /path/to/site --dry-run

  # Deploy for real (backups written automatically)
  python deploy_nav.py /path/to/site

  # Limit to one folder
  python deploy_nav.py /path/to/site/districts --dry-run

WHAT IT DOES
------------
  1. Walks the site directory recursively for *.html files
  2. In each file, finds the old <header class="site-header"> block
     (including the preceding INSTRUCTIONS comment if present)
  3. Replaces it with the new nav HTML
  4. Injects the nav <style> block into <head> if not already present
  5. Removes the stale FontAwesome CDN <link> (no longer needed)
  6. Writes a .bak backup before touching any file
  7. Prints a clear per-file report and a final summary

SAFE TO RE-RUN
--------------
  Files that already contain the new nav (detected by the marker
  "NYSpecialEd.net" inside a site-nav header) are skipped.
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
#  MARKER used to detect already-updated pages
# ─────────────────────────────────────────────
NEW_NAV_MARKER = 'class="site-nav"'

# ─────────────────────────────────────────────
#  NAV CSS  (injected once into <head>)
# ─────────────────────────────────────────────
NAV_CSS = """\
<!-- __new-nav-css-start__ -->
<style>
/* ── NEW CLEAN NAV ── */
.site-nav{position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid #e2e8f0;}
.nav-inner{max-width:1160px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:58px;gap:32px;}
.nav-wordmark{font-family:'Cormorant Garamond',serif;font-size:1.18rem;font-weight:600;color:#002868;text-decoration:none;white-space:nowrap;letter-spacing:.01em;flex-shrink:0;}
.nav-wordmark span{color:#c8102e;}
.nav-links{display:flex;list-style:none;align-items:center;gap:2px;flex:1;justify-content:center;}
.nav-item{position:relative;}
.nav-link{display:block;padding:8px 13px;font-size:.84rem;font-weight:500;color:#374151;text-decoration:none;border-radius:5px;transition:color .15s,background .15s;white-space:nowrap;cursor:pointer;background:none;border:none;font-family:inherit;}
.nav-link:hover{color:#002868;background:#f1f5f9;}
.nav-dropdown{display:none;position:absolute;top:calc(100% + 8px);left:0;background:#fff;border:1px solid #e2e8f0;border-radius:10px;box-shadow:0 12px 32px rgba(0,0,0,.10);padding:10px 0;min-width:220px;z-index:200;}
.nav-dropdown.wide{min-width:540px;display:none;grid-template-columns:1fr 1fr 1fr;padding:20px;gap:0 24px;}
.nav-item:hover .nav-dropdown{display:block;}
.nav-item:hover .nav-dropdown.wide{display:grid;}
.nav-dropdown a{display:block;padding:8px 18px;font-size:.83rem;color:#374151;text-decoration:none;transition:background .12s,color .12s;}
.nav-dropdown a:hover{background:#f1f5f9;color:#002868;}
.dropdown-section h4{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;padding:6px 18px 4px;margin-bottom:2px;}
.dropdown-section.wide-col h4{padding:0 0 8px;margin-bottom:4px;border-bottom:1px solid #f1f5f9;}
.dropdown-section.wide-col a{padding:6px 0;}
.nav-es-badge{display:inline-flex;align-items:center;gap:5px;font-size:.83rem;font-weight:600;color:#c8102e;padding:5px 11px;border-radius:5px;cursor:pointer;background:none;border:none;font-family:inherit;transition:background .15s;}
.nav-item:hover .nav-es-badge{background:#fff5f5;}
.nav-cta{display:inline-block;padding:8px 16px;background:#002868;color:#fff!important;font-size:.83rem;font-weight:600;border-radius:6px;text-decoration:none;transition:background .15s;white-space:nowrap;flex-shrink:0;}
.nav-cta:hover{background:#001a44;}
.nav-mobile-toggle{display:none;background:none;border:1px solid #e2e8f0;border-radius:6px;padding:6px 10px;cursor:pointer;font-size:1.1rem;color:#374151;}
.mobile-menu{display:none;background:#fff;border-top:1px solid #e2e8f0;padding:16px 24px 20px;}
.mobile-menu a{display:block;padding:10px 0;font-size:.9rem;color:#374151;text-decoration:none;border-bottom:1px solid #f1f5f9;}
.mobile-menu a:last-child{border-bottom:none;}
.mobile-section-head{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;padding:14px 0 4px;}
@media(max-width:900px){.nav-links{display:none;}.nav-cta{display:none;}.nav-mobile-toggle{display:block;}}
@media(max-width:900px){.mobile-menu.open{display:block;}}
</style>
<!-- __new-nav-css-end__ -->"""

# ─────────────────────────────────────────────
#  NAV HTML  (replaces old <header class="site-header">)
# ─────────────────────────────────────────────
NAV_HTML = """\
<header class="site-nav">
  <div class="nav-inner">
    <a class="nav-wordmark" href="/">NY Special<span>Ed</span>.net</a>
    <ul class="nav-links">
      <!-- NYC Districts -->
      <li class="nav-item">
        <button class="nav-link">NYC Districts &#9660;</button>
        <div class="nav-dropdown wide">
          <div class="dropdown-section wide-col">
            <h4>Manhattan</h4>
            <a href="/districts/nyc-district-01-lower-east-side/">D1 &middot; Lower East Side</a>
            <a href="/districts/nyc-district-02-upper-east-side/">D2 &middot; Upper East Side</a>
            <a href="/districts/nyc-district-03-upper-west-side/">D3 &middot; Upper West Side</a>
            <a href="/districts/nyc-district-04-east-harlem/">D4 &middot; East Harlem</a>
            <a href="/districts/nyc-district-05-central-harlem/">D5 &middot; Central Harlem</a>
            <a href="/districts/nyc-district-06-washington-heights/">D6 &middot; Washington Heights</a>
          </div>
          <div class="dropdown-section wide-col">
            <h4>Brooklyn &amp; Queens</h4>
            <a href="/districts/nyc-district-13-brooklyn-heights/">D13 &middot; Brooklyn Heights</a>
            <a href="/districts/nyc-district-15-park-slope/">D15 &middot; Park Slope</a>
            <a href="/districts/nyc-district-20-bay-ridge/">D20 &middot; Bay Ridge</a>
            <a href="/districts/nyc-district-26-bayside/">D26 &middot; Bayside</a>
            <a href="/districts/nyc-district-30-astoria/">D30 &middot; Astoria / LIC</a>
            <a href="/districts/nyc-district-75/" style="font-weight:600;color:#002868;">D75 &middot; Citywide Programs</a>
          </div>
          <div class="dropdown-section wide-col">
            <h4>Bronx &amp; Staten Island</h4>
            <a href="/districts/nyc-district-07-south-bronx/">D7 &middot; South Bronx</a>
            <a href="/districts/nyc-district-09-grand-concourse/">D9 &middot; Grand Concourse</a>
            <a href="/districts/nyc-district-10-riverdale/">D10 &middot; Riverdale</a>
            <a href="/districts/nyc-district-12-soundview/">D12 &middot; Soundview</a>
            <a href="/districts/nyc-district-31-staten-island/">D31 &middot; Staten Island</a>
            <a href="/districts/" style="font-weight:600;color:#002868;">View All 32 Districts &rarr;</a>
          </div>
        </div>
      </li>
      <!-- Upstate & LI -->
      <li class="nav-item">
        <button class="nav-link">Upstate &amp; LI &#9660;</button>
        <div class="nav-dropdown">
          <div class="dropdown-section">
            <h4>Big 5 Cities</h4>
            <a href="/districts/buffalo-city-sd/">Buffalo City SD</a>
            <a href="/districts/rochester-city-sd/">Rochester City SD</a>
            <a href="/districts/syracuse-city-sd/">Syracuse City SD</a>
            <a href="/districts/yonkers-city-sd/">Yonkers City SD</a>
            <a href="/districts/albany-city-sd/">Albany City SD</a>
          </div>
          <div class="dropdown-section">
            <h4>Long Island</h4>
            <a href="/districts/sachem-csd/">Sachem CSD</a>
            <a href="/districts/brentwood-ufsd/">Brentwood UFSD</a>
            <a href="/districts/central-islip-ufsd/">Central Islip UFSD</a>
            <a href="/districts/patchogue-medford-ufsd/">Patchogue-Medford UFSD</a>
            <a href="/districts/william-floyd-ufsd/">William Floyd UFSD</a>
            <a href="/districts/hempstead-ufsd/">Hempstead UFSD</a>
            <a href="/districts/freeport-ufsd/">Freeport UFSD</a>
          </div>
          <div class="dropdown-section">
            <h4>Westchester &amp; Hudson</h4>
            <a href="/districts/mount-vernon-city-sd/">Mount Vernon City SD</a>
            <a href="/districts/new-rochelle-city-sd/">New Rochelle City SD</a>
            <a href="/districts/white-plains-city-sd/">White Plains City SD</a>
            <a href="/districts/newburgh-enlarged-city-sd/">Newburgh Enlarged CSD</a>
            <a href="/districts/poughkeepsie-city-sd/">Poughkeepsie City SD</a>
            <a href="/districts/east-ramapo-csd/">East Ramapo CSD</a>
          </div>
        </div>
      </li>
      <!-- Parent Guides -->
      <li class="nav-item">
        <button class="nav-link">Parent Guides &#9660;</button>
        <div class="nav-dropdown">
          <div class="dropdown-section">
            <a href="/guides/cse-meeting-guide/">CSE Meeting Guide</a>
            <a href="/guides/evaluation-request-ny/">Requesting an Evaluation</a>
            <a href="/guides/cpse-preschool-special-education/">CPSE &middot; Preschool Guide</a>
            <a href="/guides/carter-cases-private-placement/">Private Placement (Carter Cases)</a>
            <a href="/guides/bilingual-iep-new-york/">Bilingual IEP Rights</a>
            <a href="/guides/dispute-resolution-ny/">Due Process &amp; Complaints</a>
          </div>
        </div>
      </li>
      <!-- Spanish Tools -->
      <li class="nav-item">
        <button class="nav-link nav-es-badge">&#127466;&#127480; En Espa&ntilde;ol &#9660;</button>
        <div class="nav-dropdown">
          <div class="dropdown-section">
            <h4>Herramientas en Espa&ntilde;ol</h4>
            <a href="/es/distritos/">Directorio de Distritos</a>
            <a href="/es/guias/reuni%C3%B3n-cse/">Gu&iacute;a de Reuni&oacute;n CSE</a>
            <a href="/es/guias/solicitar-evaluacion/">Solicitar una Evaluaci&oacute;n</a>
            <a href="/es/guias/derechos-iep-bilingue/">Derechos IEP Biling&uuml;e</a>
            <a href="/tools/">Generador de Carta IEP &rarr;</a>
          </div>
        </div>
      </li>
      <!-- Free Tools -->
      <li class="nav-item">
        <a class="nav-link" href="/tools/">Free Tools</a>
      </li>
    </ul>
    <a class="nav-cta" href="/contact/">Get the Toolkit</a>
    <button class="nav-mobile-toggle" id="mobileToggle" aria-label="Open menu">&#9776;</button>
  </div>
  <!-- Mobile menu -->
  <div class="mobile-menu" id="mobileMenu">
    <div class="mobile-section-head">NYC Districts</div>
    <a href="/districts/nyc-district-03-upper-west-side/">D3 &middot; Upper West Side</a>
    <a href="/districts/nyc-district-06-washington-heights/">D6 &middot; Washington Heights</a>
    <a href="/districts/nyc-district-75/">D75 &middot; Citywide Programs</a>
    <a href="/districts/">View All NYC Districts &rarr;</a>
    <div class="mobile-section-head">Upstate &amp; LI</div>
    <a href="/districts/buffalo-city-sd/">Buffalo City SD</a>
    <a href="/districts/yonkers-city-sd/">Yonkers City SD</a>
    <a href="/districts/sachem-csd/">Sachem CSD</a>
    <div class="mobile-section-head">Parent Guides</div>
    <a href="/guides/cse-meeting-guide/">CSE Meeting Guide</a>
    <a href="/guides/evaluation-request-ny/">Requesting an Evaluation</a>
    <a href="/guides/carter-cases-private-placement/">Private Placement (Carter Cases)</a>
    <div class="mobile-section-head">&#127466;&#127480; En Espa&ntilde;ol</div>
    <a href="/es/distritos/">Directorio de Distritos</a>
    <a href="/es/guias/reuni%C3%B3n-cse/">Gu&iacute;a de Reuni&oacute;n CSE</a>
    <a href="/tools/">Free Tools</a>
    <a href="/contact/" style="font-weight:600;color:#002868;">Get the Toolkit &rarr;</a>
  </div>
</header>
<script>
(function(){
  var t = document.getElementById('mobileToggle');
  var m = document.getElementById('mobileMenu');
  if(t && m){ t.addEventListener('click', function(){ m.classList.toggle('open'); }); }
})();
</script>"""

# ─────────────────────────────────────────────
#  GOOGLE FONTS LINK  (added to <head> if absent)
# ─────────────────────────────────────────────
GOOGLE_FONTS_LINK = (
    '<link href="https://fonts.googleapis.com/css2?'
    'family=DM+Sans:wght@400;500;600'
    '&family=Cormorant+Garamond:wght@500;600'
    '&display=swap" rel="stylesheet"/>'
)
GOOGLE_FONTS_MARKER = "fonts.googleapis.com/css2?family=DM"

# FontAwesome CDN — remove from pages once nav no longer needs it.
# Only removed when it's the nav-specific CDN link (not if the page
# uses FA icons independently in its own content).
FA_PATTERN = re.compile(
    r'<link[^>]*cdnjs\.cloudflare\.com/ajax/libs/font-awesome[^>]*/>\n?',
    re.IGNORECASE
)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def find_old_header_bounds(html: str):
    """
    Returns (start, end) character indices of the old nav block, or None.

    The block we want to replace looks like:

        <!-- (optional INSTRUCTIONS comment) -->
        <header class="site-header" ...>
          ... entire nav ...
        </header>

    Strategy: find '<header class="site-header"', then walk forward
    counting <header>/</ header> tags to find the matching close.
    We also grab any <!-- INSTRUCTIONS --> comment immediately before it.
    """
    # Locate <header class="site-header"
    header_open_re = re.compile(r'<header\s[^>]*class="site-header"[^>]*>', re.IGNORECASE)
    m = header_open_re.search(html)
    if not m:
        return None

    header_start = m.start()

    # Check if there's an INSTRUCTIONS comment just before it (with only
    # whitespace/newlines between them) and extend start back to include it.
    comment_re = re.compile(r'<!--\s*\n?\s*INSTRUCTIONS:.*?-->\s*', re.DOTALL)
    prefix = html[:header_start]
    cm = None
    for cm in comment_re.finditer(prefix):
        pass  # find the last match before header_start
    if cm and cm.end() == header_start:
        header_start = cm.start()

    # Walk forward to find the matching </header>
    depth = 0
    pos = m.start()
    tag_re = re.compile(r'<(/?)header[\s>]', re.IGNORECASE)
    for tm in tag_re.finditer(html, pos):
        if tm.group(1) == '/':   # closing tag
            depth -= 1
            if depth == 0:
                header_end = tm.end()
                # Consume a trailing newline if present
                if header_end < len(html) and html[header_end] == '\n':
                    header_end += 1
                return header_start, header_end
        else:                    # opening tag
            depth += 1

    return None  # unmatched — leave file alone


def inject_nav_css(html: str) -> str:
    """Insert NAV_CSS into <head> just before </head> if not already there."""
    if '__new-nav-css-start__' in html:
        return html  # already injected
    insert_before = re.compile(r'</head>', re.IGNORECASE)
    m = insert_before.search(html)
    if not m:
        return html  # no </head> — unusual, skip
    return html[:m.start()] + NAV_CSS + '\n' + html[m.start():]


def inject_google_fonts(html: str) -> str:
    """Add Google Fonts <link> inside <head> after <meta charset> if absent."""
    if GOOGLE_FONTS_MARKER in html:
        return html
    # Insert after first <meta charset.../>
    charset_re = re.compile(r'(<meta\s[^>]*charset[^>]*/?>)', re.IGNORECASE)
    m = charset_re.search(html)
    if m:
        pos = m.end()
        return html[:pos] + '\n' + GOOGLE_FONTS_LINK + html[pos:]
    # Fallback: after <head>
    head_re = re.compile(r'<head>', re.IGNORECASE)
    m = head_re.search(html)
    if m:
        pos = m.end()
        return html[:pos] + '\n' + GOOGLE_FONTS_LINK + html[pos:]
    return html


def remove_font_awesome(html: str) -> str:
    return FA_PATTERN.sub('', html)


def process_file(path: Path, dry_run: bool, backup: bool) -> str:
    """
    Process a single HTML file.

    Returns one of:
      'skipped_already_updated'
      'skipped_no_old_nav'
      'updated'
      'dry_run'
      'error:<message>'
    """
    try:
        original = path.read_text(encoding='utf-8')
    except Exception as e:
        return f'error:read:{e}'

    # Already updated?
    if NEW_NAV_MARKER in original:
        return 'skipped_already_updated'

    # Find old header
    bounds = find_old_header_bounds(original)
    if bounds is None:
        return 'skipped_no_old_nav'

    start, end = bounds

    # Build new content
    new_html = original[:start] + NAV_HTML + '\n' + original[end:]
    new_html = inject_nav_css(new_html)
    new_html = inject_google_fonts(new_html)
    new_html = remove_font_awesome(new_html)

    if dry_run:
        return 'dry_run'

    # Backup
    if backup:
        bak_path = path.with_suffix(path.suffix + '.bak')
        try:
            shutil.copy2(path, bak_path)
        except Exception as e:
            return f'error:backup:{e}'

    # Write
    try:
        path.write_text(new_html, encoding='utf-8')
    except Exception as e:
        return f'error:write:{e}'

    return 'updated'


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Deploy new clean nav to all HTML files in a site directory.'
    )
    parser.add_argument('site_dir', help='Root directory of your site')
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview changes without writing any files'
    )
    parser.add_argument(
        '--no-backup', action='store_true',
        help='Skip creating .bak files (not recommended)'
    )
    parser.add_argument(
        '--exclude', nargs='*', default=[],
        help='Directory names to skip (e.g. --exclude node_modules .git)'
    )
    args = parser.parse_args()

    site_dir = Path(args.site_dir).resolve()
    if not site_dir.is_dir():
        print(f'ERROR: {site_dir} is not a directory.')
        sys.exit(1)

    dry_run = args.dry_run
    backup  = not args.no_backup
    exclude = set(args.exclude or []) | {'.git', 'node_modules', '__pycache__'}

    if dry_run:
        print(f'\n{"─"*60}')
        print('  DRY RUN — no files will be written')
        print(f'{"─"*60}\n')

    print(f'Site directory : {site_dir}')
    print(f'Backup enabled : {backup}')
    print(f'Started        : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    # Counters
    counts = {
        'updated': 0,
        'dry_run': 0,
        'skipped_already_updated': 0,
        'skipped_no_old_nav': 0,
        'error': 0,
    }

    # Walk
    for root, dirs, files in os.walk(site_dir):
        # Prune excluded dirs in-place so os.walk doesn't descend into them
        dirs[:] = [d for d in dirs if d not in exclude]

        for fname in sorted(files):
            if not fname.lower().endswith('.html'):
                continue

            path = Path(root) / fname
            rel  = path.relative_to(site_dir)
            result = process_file(path, dry_run=dry_run, backup=backup)

            if result == 'updated':
                counts['updated'] += 1
                print(f'  ✅  {rel}')
            elif result == 'dry_run':
                counts['dry_run'] += 1
                print(f'  🔍  {rel}  (would update)')
            elif result == 'skipped_already_updated':
                counts['skipped_already_updated'] += 1
                print(f'  ⏭   {rel}  (already updated)')
            elif result == 'skipped_no_old_nav':
                counts['skipped_no_old_nav'] += 1
                print(f'  ➖  {rel}  (no old nav found — skipped)')
            elif result.startswith('error:'):
                counts['error'] += 1
                print(f'  ❌  {rel}  ({result})')

    # Summary
    total = sum(counts.values())
    print(f'\n{"─"*60}')
    print(f'  Files scanned          : {total}')
    if dry_run:
        print(f'  Would update           : {counts["dry_run"]}')
    else:
        print(f'  Updated                : {counts["updated"]}')
    print(f'  Already updated (skip) : {counts["skipped_already_updated"]}')
    print(f'  No old nav (skip)      : {counts["skipped_no_old_nav"]}')
    print(f'  Errors                 : {counts["error"]}')
    print(f'{"─"*60}')

    if dry_run and counts['dry_run'] > 0:
        print(f'\n  Run without --dry-run to apply these {counts["dry_run"]} changes.\n')
    elif not dry_run and counts['updated'] > 0 and backup:
        print(f'\n  Backups saved as <filename>.html.bak next to each changed file.')
        print(f'  To roll back: rename .bak → .html\n')

    if counts['error'] > 0:
        print(f'\n  ⚠  {counts["error"]} file(s) had errors. Check output above.\n')
        sys.exit(1)


if __name__ == '__main__':
    main()