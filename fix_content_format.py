#!/usr/bin/env python3
"""
fix_content_format.py
=====================
Fixes the raw-text formatting problem on every district sub-page across
all 52 district folders — and optionally in /guides/ too.

AFFECTED PAGE TYPES
───────────────────
  cse-meeting-guide.html
  evaluation-process.html
  discipline-rights.html
  special-ed-updates.html
  partners.html

WHAT IT FIXES ON EVERY PAGE
────────────────────────────
1. Wraps bare paragraphs in <p> tags         (no margins/spacing without them)
2. Converts  *   **Title:** body  bullets    (rendered as raw asterisks)
     → styled <ul class="content-list"><li> cards
3. Converts **bold** and *italic* markdown   (rendered as raw asterisks)
4. Promotes first long <h2> to <h1>          (no visible page title)
5. Injects a page header div with eyebrow    (clean entry point for readers)
6. Injects scoped CSS into <head>            (max-width, line-height, etc.)
   — also boxes "Dear Committee..." letter templates on eval pages

IDEMPOTENT — uses sentinel comments. Re-running shows "· already ok".

Usage
─────
  python fix_content_format.py                       # fix all districts
  python fix_content_format.py --dry-run             # preview only
  python fix_content_format.py --district buffalo-city-sd
  python fix_content_format.py --file path/to/page.html
  python fix_content_format.py --root "C:\\path\\to\\nyspecialed"
  python fix_content_format.py --also-guides         # also fix /guides/*.html

Requirements: Python 3.7+  (stdlib only)
"""

import argparse
import re
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE TYPE CONFIGS
#  h1=None  → promote the first <h2> to <h1> (page already has a good title)
#  h1=str   → use this fixed string as <h1>
# ══════════════════════════════════════════════════════════════════════════════

PAGE_CONFIGS: dict[str, dict] = {
    "cse-meeting-guide.html": {
        "h1":     None,   # first <h2> becomes the h1
        "intro":  "Your rights, preparation checklist, red flags, and what every "
                  "section of the IEP document means — for {district} parents.",
        "eyebrow": "{district} · CSE Meeting Guide",
    },
    "evaluation-process.html": {
        "h1":     "Requesting a Special Education Evaluation",
        "intro":  "A step-by-step guide to the 60-school-day timeline and your "
                  "rights under 8 NYCRR 200.4 and IDEA — for {district} parents.",
        "eyebrow": "{district} · Special Education Guide",
    },
    "discipline-rights.html": {
        "h1":     "Discipline Rights & the Manifestation Determination Review",
        "intro":  "What {district} parents need to know about suspension limits, "
                  "MDRs, and protecting your child's right to education under IDEA.",
        "eyebrow": "{district} · Discipline Rights",
    },
    "special-ed-updates.html": {
        "h1":     None,   # first <h2> becomes the h1
        "intro":  "Recent policy changes, district updates, and advocacy news "
                  "relevant to {district} special education families.",
        "eyebrow": "{district} · Special Ed Updates",
    },
    "partners.html": {
        "h1":     "Local Advocates, Evaluators & Legal Resources",
        "intro":  "Vetted special education advocates, neuropsychologists, and "
                  "attorneys serving {district} families.",
        "eyebrow": "{district} · Parent Resources",
    },
}

# Files that often have raw-text issues (used when --also-guides)
GUIDE_PATTERNS = [
    "cse-meeting-guide.html",
    "evaluation-request*.html",
    "evaluation-process*.html",
    "discipline-rights*.html",
    "bilingual-iep*.html",
    "dispute-resolution*.html",
    "carter-cases*.html",
    "cpse-preschool*.html",
]

# ══════════════════════════════════════════════════════════════════════════════
#  SENTINELS
# ══════════════════════════════════════════════════════════════════════════════

CSS_START = "<!-- __content-css-start__ -->"
CSS_END   = "<!-- __content-css-end__ -->"

# ══════════════════════════════════════════════════════════════════════════════
#  INJECTED CSS
# ══════════════════════════════════════════════════════════════════════════════

CONTENT_CSS = """\
<style>
/* district content styles — injected by fix_content_format.py */
.content-body {
  max-width: 780px;
  padding: 0 0 32px;
  font-size: 1.02rem;
  line-height: 1.85;
  color: #2d3748;
}
.content-body h2 {
  font-size: 1.3rem;
  color: #002868;
  border-left: 4px solid #d4af37;
  padding-left: 14px;
  margin: 44px 0 16px;
  line-height: 1.3;
}
.content-body p {
  margin: 0 0 18px;
}
/* Bullet list cards */
.content-body ul.content-list {
  margin: 8px 0 24px 0;
  padding-left: 0;
  list-style: none;
}
.content-body ul.content-list li {
  padding: 14px 18px;
  margin-bottom: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #002868;
  border-radius: 0 6px 6px 0;
  line-height: 1.75;
  font-size: 0.97rem;
}
.content-body ul.content-list li strong {
  color: #002868;
  display: block;
  margin-bottom: 4px;
}
/* Red flag callout inside list items */
.content-body .red-flag {
  display: inline-block;
  background: #fff1f2;
  color: #991b1b;
  border: 1px solid #fecaca;
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-right: 4px;
  vertical-align: middle;
}
/* Letter template blockquote */
.content-body blockquote.letter-template {
  background: #f0f4ff;
  border: 1px solid #c7d7f4;
  border-left: 5px solid #002868;
  border-radius: 0 8px 8px 0;
  padding: 24px 28px;
  margin: 24px 0 28px;
  font-size: 0.94rem;
  line-height: 1.8;
  color: #1e2d4a;
  font-style: italic;
  white-space: pre-line;
  position: relative;
}
.content-body blockquote.letter-template::before {
  content: '✉  Sample Letter';
  display: block;
  font-style: normal;
  font-weight: 700;
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #002868;
  margin-bottom: 14px;
}
/* Page header */
.content-page-header {
  padding: 8px 0 24px;
  border-bottom: 2px solid #e2e8f0;
  margin-bottom: 32px;
}
.content-page-header .eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6b7280;
  margin-bottom: 8px;
}
.content-page-header h1 {
  font-size: clamp(1.5rem, 4vw, 2.1rem);
  color: #002868;
  margin: 0 0 10px;
  line-height: 1.2;
}
.content-page-header .intro {
  font-size: 1.02rem;
  color: #4b5563;
  line-height: 1.7;
  max-width: 680px;
  margin: 0;
}
</style>"""


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def strip_sentinel(text: str, start: str, end: str) -> str:
    """Remove a sentinel block and all preceding whitespace (idempotent)."""
    return re.compile(
        r'\s*' + re.escape(start) + r'.*?' + re.escape(end),
        re.DOTALL,
    ).sub('', text)


def extract_district_name(html: str, folder_name: str) -> str:
    """Pull a human-readable district name from the page content."""
    m = re.search(r'←\s*Back to\s+(.+?)\s+Hub', html)
    if m:
        return m.group(1).strip()
    m = re.search(r'<title>[^<]*?in\s+(.+?)(?:\s*[<:])', html, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Prettify slug: "nyc-district-28-forest-hills" → "NYC District 28"
    folder = re.sub(r'^nyc-district-(\d+)-?.*', r'NYC District \1', folder_name)
    return folder.replace('-', ' ').title()


def get_page_config(filename: str) -> dict:
    """Return the config for a known page type, or a generic fallback."""
    base = Path(filename).name
    if base in PAGE_CONFIGS:
        return PAGE_CONFIGS[base]
    return {
        "h1":     None,
        "intro":  "Special education guidance for {district} parents.",
        "eyebrow": "{district} · Special Ed Guide",
    }


# ══════════════════════════════════════════════════════════════════════════════
#  DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def needs_fixing(html: str) -> bool:
    """True if the content-body has unformatted raw text."""
    if CSS_START in html:
        return False
    m = re.search(
        r'<div class="content-body"[^>]*>(.*?)(?:</div>\s*<div class="cta-box"|</main>)',
        html, re.DOTALL,
    )
    if not m:
        return False
    inner = m.group(1)
    has_bullets  = bool(re.search(r'^\*\s+\*\*', inner, re.MULTILINE))
    has_bare     = bool(re.search(r'^[A-Z][^<\n]{50,}', inner, re.MULTILINE))
    missing_p    = '<p>' not in inner
    return has_bullets or (has_bare and missing_p)


# ══════════════════════════════════════════════════════════════════════════════
#  CONTENT TRANSFORMER
# ══════════════════════════════════════════════════════════════════════════════

def fix_content(inner: str, district_name: str, filename: str) -> str:
    """
    Transform raw content-body inner HTML into properly structured HTML.

    Steps (in order):
      1. Promote first long <h2> to <h1> if config says h1=None
      2. Convert markdown bullet lists → <ul class="content-list">
      3. Box "Dear Committee..." letter templates
      4. Convert *Red Flag:* → styled badge
      5. Convert **bold** and *italic* inline markdown
      6. Wrap bare paragraphs in <p> tags
      7. Prepend page header div
    """
    cfg = get_page_config(filename)

    # ── Step 1: First <h2> → <h1>  (when h1=None in config) ──────────────
    promoted_h1 = None
    if cfg["h1"] is None:
        h2_match = re.search(r'<h2>(.+?)</h2>', inner)
        if h2_match and len(h2_match.group(1)) > 20:
            raw_title = h2_match.group(1)
            # Strip district suffix from title: "Guide in NYC District 28: ..."
            # → "Guide in NYC District 28" — keep just the first clause
            clean_title = re.split(r'\s*:\s*', raw_title)[0].strip()
            # If it's very long and district-specific, shorten to the generic part
            # e.g. "Navigating Your CSE Meeting in NYC District 28" → "Navigating Your CSE Meeting"
            clean_title = re.sub(r'\s+in\s+(NYC\s+)?District\s+\d+.*$', '', clean_title).strip()
            clean_title = re.sub(r'\s+in\s+\w[\w\s\-]+?(?:SD|City).*$', '', clean_title).strip()
            promoted_h1 = clean_title or raw_title
            # Remove the original h2 from inner
            inner = inner.replace(h2_match.group(0), '', 1)

    h1_text = promoted_h1 or cfg["h1"] or "Special Education Guide"

    # ── Step 2: Markdown bullet lists ─────────────────────────────────────
    # Handles bullets with or without blank lines between them.
    bullet_re = re.compile(r'^\*\s+\*\*(.+?)\*\*:?\s*(.*)', re.DOTALL)

    chunks_raw = re.split(r'\n{2,}', inner)
    out_chunks = []
    pending = []  # list of (title, body) tuples

    def flush_pending() -> None:
        if pending:
            out_chunks.append('<ul class="content-list">')
            for title, body in pending:
                t = title.rstrip(':').strip()
                out_chunks.append(f'  <li><strong>{t}:</strong> {body}</li>')
            out_chunks.append('</ul>')
            pending.clear()

    for chunk in chunks_raw:
        cs = chunk.strip()
        bm = bullet_re.match(cs)
        if bm:
            pending.append((bm.group(1).strip(), bm.group(2).strip()))
        else:
            flush_pending()
            if cs:
                out_chunks.append(cs)

    flush_pending()
    inner = '\n\n'.join(out_chunks)

    # ── Step 3: Letter template ────────────────────────────────────────────
    def box_letter(m):
        text = m.group(1).strip()
        text = re.sub(r'\n{2,}', '\n\n', text)
        return '<blockquote class="letter-template">\n' + text + '\n</blockquote>'

    inner = re.sub(
        r'"(Dear\s+Committee.*?(?:\[Your Name\]|Sincerely,\s*\[Your Name\]))"',
        box_letter,
        inner,
        flags=re.DOTALL,
    )

    # ── Step 4: *Red Flag:* → badge ────────────────────────────────────────
    inner = re.sub(
        r'\*Red Flag:\*\s*',
        '<span class="red-flag">⚠ Red Flag</span> ',
        inner,
    )

    # ── Step 5: Inline markdown → HTML ────────────────────────────────────
    # **bold** first, then *italic* (avoid double-processing)
    inner = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', inner)
    inner = re.sub(
        r'(?<![*<])\*(?![*\s])([^*\n<>]{1,140}?)(?<!\s)\*(?![*>])',
        r'<em>\1</em>',
        inner,
    )

    # ── Step 6: Wrap bare text in <p> ─────────────────────────────────────
    BLOCK_START = re.compile(
        r'^\s*<(h[1-6]|ul|ol|li|blockquote|div|pre|table|figure|aside|nav)',
        re.IGNORECASE,
    )
    BLOCK_CLOSE = re.compile(r'^\s*</', re.IGNORECASE)

    chunks = re.split(r'\n{2,}', inner)
    wrapped = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if BLOCK_START.match(chunk) or BLOCK_CLOSE.match(chunk):
            wrapped.append(chunk)
        else:
            wrapped.append(f'<p>{chunk}</p>')

    inner = '\n\n'.join(wrapped)

    # ── Step 7: Page header ────────────────────────────────────────────────
    eyebrow = cfg["eyebrow"].format(district=district_name)
    intro   = cfg["intro"].format(district=district_name)
    page_header = (
        f'<div class="content-page-header">\n'
        f'  <div class="eyebrow">{eyebrow}</div>\n'
        f'  <h1>{h1_text}</h1>\n'
        f'  <p class="intro">{intro}</p>\n'
        f'</div>\n'
    )

    return page_header + inner


# ══════════════════════════════════════════════════════════════════════════════
#  FILE PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════

def process_file(filepath: Path, dry_run: bool) -> str:
    """
    Process one HTML file.
    Returns: 'fixed' | 'already_fixed' | 'no_content_body' | 'error:<msg>'
    """
    try:
        original = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return f'error:{e}'

    if not needs_fixing(original):
        return 'already_fixed'

    # Find content-body
    content_match = re.search(
        r'(<div class="content-body"[^>]*>)(.*?)(<\/div>\s*<div class="cta-box")',
        original, re.DOTALL,
    )
    if not content_match:
        # Fallback: no cta-box
        content_match = re.search(
            r'(<div class="content-body"[^>]*>)(.*?)(<\/div>\s*<\/main>)',
            original, re.DOTALL,
        )
    if not content_match:
        return 'no_content_body'

    district_name = extract_district_name(original, filepath.parent.name)
    new_inner     = fix_content(content_match.group(2), district_name, filepath.name)

    new_block = (
        content_match.group(1)
        + '\n' + new_inner + '\n'
        + content_match.group(3)
    )
    html = original.replace(content_match.group(0), new_block, 1)

    # Inject CSS
    html = strip_sentinel(html, CSS_START, CSS_END)
    css_block = f'{CSS_START}\n{CONTENT_CSS}\n{CSS_END}'
    html = re.sub(r'\s*</head>', f'\n{css_block}\n</head>', html, count=1)

    if html == original:
        return 'already_fixed'

    if not dry_run:
        filepath.write_text(html, encoding='utf-8')

    return 'fixed'


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Fix raw-text formatting on district sub-pages sitewide.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        '--root',
        default=r'C:\Users\elisa\OneDrive\Documents\github\nyspecialed',
        help='Project root (default: %(default)s)',
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview without writing')
    parser.add_argument('--district', default=None, metavar='SLUG',
                        help='Single district only (e.g. buffalo-city-sd)')
    parser.add_argument('--also-guides', action='store_true',
                        help='Also fix matching pages in /guides/')
    parser.add_argument('--file', default=None, metavar='PATH',
                        help='Process a single specific file')
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        root = Path.cwd()
        print(f'  ⚠  Root not found — using CWD: {root}')

    if args.dry_run:
        print('── DRY RUN ── no files will be written\n')

    # ── Build target list ─────────────────────────────────────────────────
    targets: list[Path] = []

    if args.file:
        targets = [Path(args.file)]

    else:
        districts_path = root / 'districts'

        candidate_dirs: list[Path] = []
        if args.district:
            d = districts_path / args.district
            if not d.exists():
                print(f'  ✗  District not found: {d}')
                sys.exit(1)
            candidate_dirs = [d]
        elif districts_path.exists():
            candidate_dirs = sorted(
                d for d in districts_path.iterdir() if d.is_dir()
            )

        for d in candidate_dirs:
            for page in PAGE_CONFIGS:
                f = d / page
                if f.exists():
                    targets.append(f)

        if args.also_guides:
            guides_path = root / 'guides'
            if guides_path.exists():
                import fnmatch
                for pattern in GUIDE_PATTERNS:
                    for f in sorted(guides_path.glob(pattern)):
                        if f not in targets:
                            targets.append(f)

    if not targets:
        print('  ⚠  No target files found. Check --root.')
        sys.exit(0)

    # ── Process ──────────────────────────────────────────────────────────
    print(f'\n{"═" * 60}')
    print(f'  Fixing district content pages  ({len(targets)} files)')
    print(f'{"═" * 60}')

    counts = {'fixed': 0, 'already_fixed': 0, 'no_content_body': 0, 'error': 0}

    for fp in targets:
        rel = fp
        try:
            rel = fp.relative_to(root)
        except ValueError:
            pass

        result = process_file(fp, args.dry_run)

        if result == 'fixed':
            verb = '~ would fix' if args.dry_run else '✓ fixed'
            print(f'  {verb:<14}  {rel}')
            counts['fixed'] += 1
        elif result == 'already_fixed':
            print(f'  · already ok     {rel}')
            counts['already_fixed'] += 1
        elif result == 'no_content_body':
            print(f'  ⚠ no content-body  {rel}')
            counts['no_content_body'] += 1
        else:
            print(f'  ✗ {result}')
            counts['error'] += 1

    # ── Summary ──────────────────────────────────────────────────────────
    verb = 'would be ' if args.dry_run else ''
    print(f'\n{"═" * 60}')
    print(f'  Pages {verb}fixed        : {counts["fixed"]}')
    print(f'  Already formatted    : {counts["already_fixed"]}')
    if counts['no_content_body']:
        print(f'  No content-body      : {counts["no_content_body"]}  ← check manually')
    if counts['error']:
        print(f'  Errors               : {counts["error"]}')
    print(f'{"═" * 60}')

    if not args.dry_run and counts['fixed'] > 0:
        print()
        print('  ✅  Done. Run --dry-run to preview future changes.')
        print()


if __name__ == '__main__':
    main()