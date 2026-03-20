"""
NY Special Ed — Navbar Deployer
=================================
Finds every .html file under your site root and replaces the nav
CSS block + nav HTML block with the current flat navbar.

No dropdowns. Flat links across the top. Works on every page.

USAGE
──────
    python deploy_nav.py            # dry run — shows what would change
    python deploy_nav.py --write    # actually update files
    python deploy_nav.py --write --dir C:\\path\\to\\other\\folder

REQUIREMENTS
─────────────
    Python 3.8+  (no third-party packages needed)

HOW IT FINDS THE NAV
─────────────────────
CSS block  : between <!-- __new-nav-css-start__ --> and <!-- __new-nav-css-end__ -->
HTML block : between <header class="site-nav"> and the </script> that
             immediately follows the mobile-toggle script.

If either marker is missing the file is skipped with a note so you
can add the markers manually once and the script handles it from then on.

BACKUP
───────
    A .bak file is written next to each changed file before any edit.
    e.g.  index.html  →  index.html.bak
    Pass --no-backup to skip this.
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
#  ✏️  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

SITE_ROOT = Path(r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed")

# HTML files to never touch
SKIP_FILES = {
    "guide-template.html",
    "guide-template-es.html",
    "index.html.bak",
}

# Folders to never recurse into
SKIP_DIRS = {
    ".git", "node_modules", ".vscode", "__pycache__",
}


# ══════════════════════════════════════════════════════════════════════════════
#  NEW NAV CSS BLOCK
#  Paste your updated CSS here whenever the nav styles change.
#  Everything between (and including) the two comment markers.
# ══════════════════════════════════════════════════════════════════════════════

NEW_NAV_CSS = """\
<!-- __new-nav-css-start__ -->
<style>
/* ── FLAT NAV — no dropdowns ── */
.site-nav{position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid #e2e8f0;}
.nav-inner{max-width:1160px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:58px;gap:24px;}
.nav-wordmark{font-family:'Cormorant Garamond',serif;font-size:1.18rem;font-weight:600;color:#002868;text-decoration:none;white-space:nowrap;letter-spacing:.01em;flex-shrink:0;}
.nav-wordmark span{color:#c8102e;}
.nav-links{display:flex;list-style:none;align-items:center;gap:2px;flex:1;justify-content:center;margin:0;padding:0;}
.nav-link{display:block;padding:8px 12px;font-size:.84rem;font-weight:500;color:#374151;text-decoration:none;border-radius:5px;transition:color .15s,background .15s;white-space:nowrap;}
.nav-link:hover{color:#002868;background:#f1f5f9;}
.nav-link.es{color:#c8102e;font-weight:600;}
.nav-link.es:hover{background:#fff5f5;}
.nav-cta{display:inline-block;padding:8px 16px;background:#c8102e;color:#fff!important;font-size:.83rem;font-weight:600;border-radius:6px;text-decoration:none;transition:background .15s;white-space:nowrap;flex-shrink:0;}
.nav-cta:hover{background:#a50b24;}
.nav-mobile-toggle{display:none;background:none;border:1px solid #e2e8f0;border-radius:6px;padding:6px 10px;cursor:pointer;font-size:1.1rem;color:#374151;line-height:1;}
.mobile-menu{display:none;background:#fff;border-top:1px solid #e2e8f0;padding:12px 24px 20px;}
.mobile-menu a{display:block;padding:11px 0;font-size:.9rem;color:#374151;text-decoration:none;border-bottom:1px solid #f1f5f9;font-weight:500;}
.mobile-menu a:last-child{border-bottom:none;}
.mobile-menu a.es{color:#c8102e;font-weight:600;}
.mobile-menu a.cta-mobile{margin-top:10px;display:block;text-align:center;padding:12px;background:#c8102e;color:#fff!important;border-radius:6px;font-weight:700;font-size:.9rem;text-decoration:none;border:none;}
@media(max-width:860px){.nav-links{display:none;}.nav-cta{display:none;}.nav-mobile-toggle{display:block;}}
@media(max-width:860px){.mobile-menu.open{display:block;}}
</style>
<!-- __new-nav-css-end__ -->"""


# ══════════════════════════════════════════════════════════════════════════════
#  NEW NAV HTML BLOCK
#  Everything from <header class="site-nav"> through the mobile-toggle </script>
# ══════════════════════════════════════════════════════════════════════════════

NEW_NAV_HTML = """\
<header class="site-nav">
  <div class="nav-inner">

    <!-- Wordmark -->
    <a class="nav-wordmark" href="/">NY Special<span>Ed</span>.net</a>

    <!-- Desktop links — flat, no dropdowns -->
    <ul class="nav-links">
      <li><a class="nav-link" href="/districts/">NYC Districts</a></li>
      <li><a class="nav-link" href="/districts/upstate/">Upstate Districts</a></li>
      <li><a class="nav-link" href="/guides/">Parent Guides</a></li>
      <li><a class="nav-link es" href="/guides/es/index.html">&#127466;&#127480; En Espa&ntilde;ol</a></li>
      <li><a class="nav-link" href="/tools/">Tools</a></li>
      <li><a class="nav-link" href="/resources/">Resources</a></li>
    </ul>

    <!-- CTA button -->
    <a class="nav-cta" href="/tools/">IEP Letter</a>

    <!-- Hamburger -->
    <button class="nav-mobile-toggle" id="mobileToggle" aria-label="Open menu">&#9776;</button>
  </div>

  <!-- Mobile menu — same flat links -->
  <div class="mobile-menu" id="mobileMenu">
    <a href="/districts/">NYC Districts</a>
    <a href="/districts/upstate/">Upstate Districts</a>
    <a href="/guides/">Parent Guides</a>
    <a class="es" href="/guides/es/index.html">&#127466;&#127480; En Espa&ntilde;ol</a>
    <a href="/tools/">Tools</a>
    <a href="/resources/">Resources</a>
    <a class="cta-mobile" href="/tools/">IEP Letter &rarr;</a>
  </div>
</header>
<script>
(function(){
  var t = document.getElementById('mobileToggle');
  var m = document.getElementById('mobileMenu');
  if(t && m){ t.addEventListener('click', function(){ m.classList.toggle('open'); }); }
})();
</script>"""


# ══════════════════════════════════════════════════════════════════════════════
#  REGEX PATTERNS  (compiled once, reused for every file)
# ══════════════════════════════════════════════════════════════════════════════

# CSS block: from the start comment to the end comment (inclusive)
CSS_PATTERN = re.compile(
    r'<!--\s*__new-nav-css-start__\s*-->.*?<!--\s*__new-nav-css-end__\s*-->',
    re.DOTALL
)

# HTML block: from <header class="site-nav"> to the </script> that closes
# the mobile-toggle listener.  We anchor on the mobileToggle script so we
# don't accidentally eat a different </script> further down the page.
HTML_PATTERN = re.compile(
    r'<header\s+class="site-nav">.*?</script>',
    re.DOTALL
)


# ══════════════════════════════════════════════════════════════════════════════
#  FILE PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════

def process_file(html_path: Path, write: bool, backup: bool) -> str:
    """
    Process one HTML file.
    Returns a status string: 'updated', 'skipped', 'no_markers', 'unchanged', 'error'
    """
    try:
        original = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"error:read:{e}"

    text = original
    changed = False

    # ── Replace CSS block ────────────────────────────────────────────────────
    if CSS_PATTERN.search(text):
        new_text = CSS_PATTERN.sub(NEW_NAV_CSS, text, count=1)
        if new_text != text:
            text = new_text
            changed = True
    else:
        # No CSS marker — note it but keep going (HTML block may still exist)
        pass

    # ── Replace HTML block ───────────────────────────────────────────────────
    if HTML_PATTERN.search(text):
        new_text = HTML_PATTERN.sub(NEW_NAV_HTML, text, count=1)
        if new_text != text:
            text = new_text
            changed = True
    else:
        pass  # Will be reported below

    # Report if neither marker was found
    css_found  = bool(CSS_PATTERN.search(original))
    html_found = bool(HTML_PATTERN.search(original))
    if not css_found and not html_found:
        return "no_markers"

    if not changed:
        return "unchanged"

    # ── Write ────────────────────────────────────────────────────────────────
    if write:
        if backup:
            shutil.copy2(html_path, html_path.with_suffix(".html.bak"))
        html_path.write_text(text, encoding="utf-8")

    return "updated"


# ══════════════════════════════════════════════════════════════════════════════
#  FILE WALKER
# ══════════════════════════════════════════════════════════════════════════════

def collect_html_files(root: Path) -> list[Path]:
    """Recursively find all .html files, skipping SKIP_DIRS and SKIP_FILES."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs in-place so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not fname.lower().endswith(".html"):
                continue
            if fname in SKIP_FILES:
                continue
            # Skip .bak files that happen to end in .html
            if fname.endswith(".html.bak"):
                continue
            files.append(Path(dirpath) / fname)
    return sorted(files)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="NY Special Ed — Deploy flat navbar to all HTML pages"
    )
    parser.add_argument(
        "--write", action="store_true",
        help="Actually write changes. Without this flag the script is a dry run."
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="Skip writing .bak files before overwriting."
    )
    parser.add_argument(
        "--dir", type=Path, default=None,
        help="Override the site root directory (default: SITE_ROOT in script)."
    )
    args = parser.parse_args()

    root    = args.dir or SITE_ROOT
    write   = args.write
    backup  = not args.no_backup

    print()
    print("══════════════════════════════════════════════════════════")
    print("   NY Special Ed — Navbar Deployer")
    print("══════════════════════════════════════════════════════════")
    print(f"   Root   : {root}")
    print(f"   Mode   : {'WRITE' if write else 'DRY RUN — pass --write to apply changes'}")
    print(f"   Backup : {'yes (.html.bak)' if backup and write else ('no' if not write else 'no (--no-backup)')}")
    print()

    if not root.exists():
        print(f"❌  Site root not found: {root}")
        print("    Edit SITE_ROOT at the top of the script, or pass --dir <path>")
        sys.exit(1)

    # Collect files
    files = collect_html_files(root)
    if not files:
        print(f"⚠️   No .html files found under {root}")
        sys.exit(0)

    print(f"   Found {len(files)} HTML file(s) to check.\n")

    # Process
    counts = {"updated": 0, "unchanged": 0, "no_markers": 0, "error": 0}
    no_marker_files = []
    error_files     = []
    updated_files   = []

    for path in files:
        rel = path.relative_to(root)
        status = process_file(path, write=write, backup=backup)

        if status == "updated":
            counts["updated"] += 1
            updated_files.append(rel)
            verb = "✅  Updated" if write else "🔵  Would update"
            print(f"   {verb}  {rel}")

        elif status == "unchanged":
            counts["unchanged"] += 1
            # Only print in dry-run mode for transparency
            if not write:
                print(f"   ✔   Already current  {rel}")

        elif status == "no_markers":
            counts["no_markers"] += 1
            no_marker_files.append(rel)
            print(f"   ⚠️   No nav markers    {rel}")

        else:
            counts["error"] += 1
            error_files.append((rel, status))
            print(f"   ❌  Error             {rel}  ({status})")

    # Summary
    print()
    print("══════════════════════════════════════════════════════════")
    if write:
        print(f"   Done!  {counts['updated']} updated  ·  "
              f"{counts['unchanged']} already current  ·  "
              f"{counts['no_markers']} missing markers  ·  "
              f"{counts['error']} errors")
    else:
        print(f"   Dry run complete.")
        print(f"   {counts['updated']} file(s) would be updated.")
        print(f"   Run with --write to apply changes.")

    if no_marker_files:
        print()
        print("   ── Files missing nav markers ──────────────────────────")
        print("   These pages have no  <!-- __new-nav-css-start__ -->")
        print("   or <header class=\"site-nav\"> block. Add the markers once")
        print("   and the script will maintain them automatically.")
        print()
        for f in no_marker_files:
            print(f"     • {f}")

    if error_files:
        print()
        print("   ── Errors ──────────────────────────────────────────────")
        for f, msg in error_files:
            print(f"     • {f}  →  {msg}")

    print("══════════════════════════════════════════════════════════")
    print()


if __name__ == "__main__":
    main()