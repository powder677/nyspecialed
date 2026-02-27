#!/usr/bin/env python3
"""
fix_evaluation_format.py
========================
Fixes the raw-text formatting problem on every evaluation-process.html
page across all district folders (and any matching guide pages).

WHAT IT FIXES
─────────────
1. Wraps bare paragraphs in <p> tags              (text had no margins/spacing)
2. Converts markdown bullets (* **Title:**) to    (showed as literal asterisks)
   styled <ul><li> HTML cards
3. Converts **bold** and *italic* markdown        (showed as asterisks)
4. Boxes the sample referral letter template       (was buried in body text)
5. Adds a page <h1> + intro line                  (no visible page title)
6. Injects scoped CSS for content readability     (max-width, line-height, etc.)

IDEMPOTENT — runs the same sentinel comment strategy as fix_district_nav.py.
Safe to run multiple times; pages already fixed will show "· no change".

Usage
─────
  python fix_evaluation_format.py                   # fix all districts
  python fix_evaluation_format.py --dry-run         # preview only
  python fix_evaluation_format.py --district buffalo-city-sd
  python fix_evaluation_format.py --root "C:\\path\\to\\nyspecialed"
  python fix_evaluation_format.py --also-guides     # also fix guides/*.html

Requirements: Python 3.7+  (stdlib only)
"""

import argparse
import re
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
#  SENTINELS  (idempotency — same pattern as fix_district_nav.py)
# ══════════════════════════════════════════════════════════════════════════════

CSS_START = "<!-- __eval-css-start__ -->"
CSS_END   = "<!-- __eval-css-end__ -->"

# ══════════════════════════════════════════════════════════════════════════════
#  SCOPED CSS injected into <head>
# ══════════════════════════════════════════════════════════════════════════════

EVAL_CSS = """\
<style>
/* evaluation-process content styles — injected by fix_evaluation_format.py */
.content-body {
  max-width: 780px;
  padding: 0 0 32px;
  font-size: 1.02rem;
  line-height: 1.8;
  color: #2d3748;
}
.content-body h2 {
  font-size: 1.35rem;
  color: #002868;
  border-left: 4px solid #d4af37;
  padding-left: 14px;
  margin: 44px 0 16px;
  line-height: 1.3;
}
.content-body p {
  margin: 0 0 18px;
}
.content-body ul.eval-list {
  margin: 8px 0 24px 0;
  padding-left: 0;
  list-style: none;
}
.content-body ul.eval-list li {
  padding: 14px 18px;
  margin-bottom: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #002868;
  border-radius: 0 6px 6px 0;
  line-height: 1.7;
  font-size: 0.97rem;
}
.content-body ul.eval-list li strong {
  color: #002868;
  display: block;
  margin-bottom: 4px;
}
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
  content: '✉  Sample Referral Letter';
  display: block;
  font-style: normal;
  font-weight: 700;
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #002868;
  margin-bottom: 14px;
}
.eval-page-header {
  padding: 8px 0 24px;
  border-bottom: 2px solid #e2e8f0;
  margin-bottom: 32px;
}
.eval-page-header .eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6b7280;
  margin-bottom: 8px;
}
.eval-page-header h1 {
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  color: #002868;
  margin: 0 0 10px;
  line-height: 1.2;
}
.eval-page-header .intro {
  font-size: 1.05rem;
  color: #4b5563;
  line-height: 1.7;
  max-width: 680px;
  margin: 0;
}
</style>"""


# ══════════════════════════════════════════════════════════════════════════════
#  CONTENT FIXER  — pure text transformation, no BeautifulSoup needed
# ══════════════════════════════════════════════════════════════════════════════


def fix_content_body(inner: str, district_name: str) -> str:
    """
    Transform raw unformatted content-body inner HTML into properly structured HTML.
    Steps applied in order:
      1. Convert markdown bullet lists → <ul class="eval-list">
      2. Box letter templates → <blockquote class="letter-template">
      3. Convert **bold** and *italic* inline markdown
      4. Wrap bare text paragraphs in <p> tags
      5. Prepend a page <h1> header
    """

    # ── Step 1: Markdown bullet lists ─────────────────────────────────────
    # Bullets may be separated by blank lines (chunk-by-chunk detection).
    # Handles both:
    #   *   **Title:** body   (colon outside the **)
    #   *   **Title:**        (colon inside the ** — common in real pages)
    bullet_re = re.compile(r'^\*\s+\*\*(.+?)\*\*:?\s*(.*)', re.DOTALL)

    chunks_raw = re.split(r'\n{2,}', inner)
    out_chunks = []
    pending = []   # list of (title, body)

    def flush_pending():
        if pending:
            out_chunks.append('<ul class="eval-list">')
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

    # ── Step 2: Letter template  "Dear ... Sincerely, [Your Name]" ──────
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

    # ── Step 3: Inline markdown → HTML ────────────────────────────────────
    inner = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', inner)
    inner = re.sub(r'(?<![*<])\*(?![*\s])([^*\n<>]{1,120}?)(?<!\s)\*(?![*>])', r'<em>\1</em>', inner)

    # ── Step 4: Wrap bare text paragraphs in <p> ──────────────────────────
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

    # ── Step 5: Page header ────────────────────────────────────────────────
    eyebrow = f'{district_name} · Special Education Guide'
    page_header = (
        f'<div class="eval-page-header">\n'
        f'  <div class="eyebrow">{eyebrow}</div>\n'
        f'  <h1>Requesting a Special Education Evaluation</h1>\n'
        f'  <p class="intro">A step-by-step guide to your rights, the 60-school-day '
        f'timeline, and what evaluations {district_name} must conduct under '
        f'8 NYCRR 200.4 and IDEA.</p>\n'
        f'</div>\n'
    )

    return page_header + inner


# ══════════════════════════════════════════════════════════════════════════════
#  DETECTION: is this page already fixed?
# ══════════════════════════════════════════════════════════════════════════════

def needs_fixing(html: str) -> bool:
    """
    Return True if the content-body still has unformatted content.
    Checks for the three most reliable signals of an unfixed page.
    """
    # Already has our sentinel CSS → skip
    if CSS_START in html:
        return False

    m = re.search(
        r'<div class="content-body"[^>]*>(.*?)(?:</div>\s*<div class="cta-box"|</main>)',
        html, re.DOTALL
    )
    if not m:
        return False

    inner = m.group(1)
    has_raw_bullets   = bool(re.search(r'^\*\s+\*\*', inner, re.MULTILINE))
    has_bare_text     = bool(re.search(r'^[A-Z][^<\n]{40,}', inner, re.MULTILINE))
    missing_p_tags    = '<p>' not in inner

    return has_raw_bullets or (has_bare_text and missing_p_tags)


# ══════════════════════════════════════════════════════════════════════════════
#  DISTRICT NAME EXTRACTOR
# ══════════════════════════════════════════════════════════════════════════════

def extract_district_name(html: str, folder_name: str) -> str:
    """
    Try to pull a clean district name from the page <title> or the
    aeo-authority-block back-link. Falls back to prettifying the folder name.
    """
    # Try: aeo-authority-block  "← Back to Buffalo City SD Hub"
    m = re.search(r'←\s*Back to\s+(.+?)\s+Hub', html)
    if m:
        return m.group(1).strip()

    # Try: <title>Requesting an Evaluation in District 28</title>
    m = re.search(r'<title>[^<]*?in\s+(.+?)</title>', html, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Try: meta description "...evaluation timeline in District 28."
    m = re.search(r'timeline in\s+(.+?)\.', html)
    if m:
        return m.group(1).strip()

    # Fallback: prettify folder name
    # "nyc-district-28-forest-hills" → "NYC District 28"
    folder = folder_name
    folder = re.sub(r'^nyc-district-(\d+)-?.*', r'NYC District \1', folder)
    folder = folder.replace('-', ' ').title()
    return folder


# ══════════════════════════════════════════════════════════════════════════════
#  STRIP SENTINEL (idempotency helper — same as other scripts)
# ══════════════════════════════════════════════════════════════════════════════

def strip_sentinel(text: str, start: str, end: str) -> str:
    """Remove a sentinel block including any preceding whitespace."""
    return re.compile(
        r'\s*' + re.escape(start) + r'.*?' + re.escape(end),
        re.DOTALL,
    ).sub('', text)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PAGE PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════

def process_file(filepath: Path, dry_run: bool) -> str:
    """
    Process one evaluation-process.html file.
    Returns: 'fixed' | 'already_fixed' | 'no_content_body' | 'error'
    """
    try:
        original = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return f'error:{e}'

    if not needs_fixing(original):
        return 'already_fixed'

    # ── Find the content-body block ───────────────────────────────────────
    content_match = re.search(
        r'(<div class="content-body"[^>]*>)(.*?)(<\/div>\s*<div class="cta-box")',
        original,
        re.DOTALL,
    )

    if not content_match:
        # Try alternate ending (no cta-box — ends at </main>)
        content_match = re.search(
            r'(<div class="content-body"[^>]*>)(.*?)(<\/div>\s*<\/main>)',
            original,
            re.DOTALL,
        )

    if not content_match:
        return 'no_content_body'

    # ── Get district name ─────────────────────────────────────────────────
    folder_name = filepath.parent.name
    district_name = extract_district_name(original, folder_name)

    # ── Fix the content ───────────────────────────────────────────────────
    old_inner   = content_match.group(2)
    new_inner   = fix_content_body(old_inner, district_name)

    # Rebuild the content div (keep original opening tag and trailing anchor)
    new_block = (
        content_match.group(1)          # <div class="content-body" ...>
        + '\n' + new_inner + '\n'
        + content_match.group(3)        # </div><div class="cta-box" ...
    )

    html = original.replace(content_match.group(0), new_block, 1)

    # ── Strip any old CSS sentinel, inject fresh ──────────────────────────
    html = strip_sentinel(html, CSS_START, CSS_END)
    css_block = f'{CSS_START}\n{EVAL_CSS}\n{CSS_END}'
    html = re.sub(r'\s*</head>', f'\n{css_block}\n</head>', html, count=1)

    if html == original:
        return 'already_fixed'

    if not dry_run:
        filepath.write_text(html, encoding='utf-8')

    return 'fixed'


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Fix evaluation-process.html formatting across all district folders.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        '--root',
        default=r'C:\Users\elisa\OneDrive\Documents\github\nyspecialed',
        help='Project root directory (default: %(default)s)',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview changes without writing files',
    )
    parser.add_argument(
        '--district',
        default=None,
        metavar='SLUG',
        help='Process a single district folder only (e.g. buffalo-city-sd)',
    )
    parser.add_argument(
        '--also-guides', action='store_true',
        help='Also fix evaluation-related pages in /guides/',
    )
    parser.add_argument(
        '--file',
        default=None,
        metavar='PATH',
        help='Process a single specific HTML file (for testing)',
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        root = Path.cwd()
        print(f'  ⚠  Root not found — falling back to CWD: {root}')

    if args.dry_run:
        print('── DRY RUN ── no files will be written\n')

    # ── Build the list of files to process ───────────────────────────────
    targets: list[Path] = []

    if args.file:
        # Single file mode
        targets = [Path(args.file)]

    else:
        districts_path = root / 'districts'

        if args.district:
            # Single district
            d = districts_path / args.district
            if not d.exists():
                print(f'  ✗  District folder not found: {d}')
                sys.exit(1)
            ev = d / 'evaluation-process.html'
            if ev.exists():
                targets.append(ev)
            else:
                print(f'  ✗  No evaluation-process.html in {d}')
                sys.exit(1)

        elif districts_path.exists():
            # All districts
            for d in sorted(districts_path.iterdir()):
                if d.is_dir():
                    ev = d / 'evaluation-process.html'
                    if ev.exists():
                        targets.append(ev)

        if args.also_guides:
            guides_path = root / 'guides'
            if guides_path.exists():
                # Pick up evaluation-related guide pages
                for f in sorted(guides_path.glob('evaluation*.html')):
                    targets.append(f)
                for f in sorted(guides_path.glob('*evaluation*.html')):
                    if f not in targets:
                        targets.append(f)

    if not targets:
        print('  ⚠  No evaluation-process.html files found. Check --root path.')
        sys.exit(0)

    # ── Process ──────────────────────────────────────────────────────────
    print(f'\n{"═" * 60}')
    print(f'  Fixing evaluation-process.html  ({len(targets)} files)')
    print(f'{"═" * 60}')

    counts = {'fixed': 0, 'already_fixed': 0, 'no_content_body': 0, 'error': 0}

    for filepath in targets:
        rel = filepath
        try:
            rel = filepath.relative_to(root)
        except ValueError:
            pass

        result = process_file(filepath, args.dry_run)

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
    print(f'  Pages {verb}fixed    : {counts["fixed"]}')
    print(f'  Already formatted  : {counts["already_fixed"]}')
    if counts['no_content_body']:
        print(f'  No content-body    : {counts["no_content_body"]}  ← check these manually')
    if counts['error']:
        print(f'  Errors             : {counts["error"]}')
    print(f'{"═" * 60}')

    if not args.dry_run and counts['fixed'] > 0:
        print()
        print('  ✅  Done. Run with --dry-run to preview future changes.')
        print()


if __name__ == '__main__':
    main()