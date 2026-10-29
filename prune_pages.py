#!/usr/bin/env python3
"""
prune_pages.py - remove thin programmatic subpages and clean up every reference to them.

What it does
------------
1. Finds the pages to prune: districts/**/<template>.html for each template name
   (default: partners, what-is-an-iep - the two templates with 0 clicks in the
   Mar-Sep 2026 Search Console data).
2. Skips ("protects") any page that earned clicks in the Search Console Pages
   exports you pass with --protect-csv.
3. Cleans every HTML file that links to a pruned page:
     - <li><a href="pruned">..</a></li>   -> whole <li> removed
     - <a href="pruned"> anywhere inside a <nav>...</nav> block -> link removed
     - <div class="insight-box"> call-to-action blocks whose links all point at pruned pages
       -> whole block (and the comment above it) removed
     - <a href="pruned"> that wraps a heading/paragraph/div (a "card") -> whole card removed
     - any other <a href="pruned">text</a> -> unwrapped to plain text (logged as REVIEW,
       with surrounding context in changes.csv so you can spot patterns)
     - <link rel="alternate" href="pruned"> (hreflang) -> removed
4. Removes pruned URLs (and alternates pointing at them) from sitemap*.xml.
5. Deletes the pruned files (a backup copy is kept).
6. Writes redirect rules (301 to the district hub) so old URLs and any
   external links pass value to the hub instead of 404ing.
7. Re-scans the whole site and lists anything still mentioning a pruned URL
   (JSON-LD breadcrumbs, JSON data files, llms.txt, etc.) for manual review.

Safe by default: it is a DRY RUN unless you pass --apply.

Usage
-----
  # preview
  python prune_pages.py --root ./site --protect-csv Pages_a4d0c7.csv Pages_1.csv

  # do it
  python prune_pages.py --root ./site --protect-csv Pages_a4d0c7.csv Pages_1.csv --apply

  # also prune other templates / explicit URLs
  python prune_pages.py --root ./site --templates partners what-is-an-iep special-ed-updates \
      --urls-file extra_urls.txt

Run it on the folder that holds the final .html files (or on your source if it is
plain static HTML). If the site is generated from templates/a CMS, make the same
change in the generator, otherwise the pages come back on the next build.
Keep the site in git so you can review the diff.
"""
import argparse
import csv
import html
import posixpath
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

DEFAULT_TEMPLATES = ["partners", "what-is-an-iep"]
DEFAULT_CTA_CLASSES = ["insight-box"]
DEFAULT_HOSTS = ["www.newyorkspecialed.net", "newyorkspecialed.net"]
TEXT_EXTS = {".html", ".htm", ".xhtml", ".xml", ".txt", ".json", ".js", ".md", ".webmanifest"}
HTML_EXTS = {".html", ".htm", ".xhtml"}

SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML_NS = "http://www.w3.org/1999/xhtml"

# <li> that contains nothing but a single link
LI_RE = re.compile(
    r"<li\b[^>]*>\s*(<a\b[^>]*>(?:(?!</a>).)*</a>)\s*</li>[ \t]*(?:\r?\n)?", re.I | re.S
)
A_RE = re.compile(r"<a\b([^>]*)>((?:(?!</a>).)*)</a>", re.I | re.S)
NAV_RE = re.compile(r"<nav\b.*?</nav>", re.I | re.S)
A_LINE_RE = re.compile(r"<a\b([^>]*)>((?:(?!</a>).)*)</a>[ \t]*(?:\r?\n)?", re.I | re.S)
BLOCK_RE = re.compile(r"<(?:h[1-6]|p|div|ul|ol|li|section|article|img)\b", re.I)
LINK_RE = re.compile(r"<link\b[^>]*>[ \t]*\n?", re.I)
HREF_RE = re.compile(r"""\bhref\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
OPEN_A_RE = re.compile(r"<a\b[^>]*>", re.I)
DIV_TOKEN = re.compile(r"<div\b[^>]*>|</div\s*>", re.I)


# --------------------------------------------------------------------------- helpers
def normalize(href, base_path, hosts):
    """Return a normalized site path ('/districts/x/partners.html') or None if external/non-page."""
    if not href:
        return None
    href = html.unescape(href).strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    u = urlparse(href)
    if u.scheme in ("http", "https"):
        if u.netloc.lower() not in hosts:
            return None
    elif u.scheme:
        return None
    elif href.startswith("//") and u.netloc.lower() not in hosts:
        return None
    path = unquote(u.path)
    if not path:
        return None
    if not path.startswith("/"):
        path = posixpath.join(posixpath.dirname(base_path), path)
    return posixpath.normpath(path)


def get_href(tag_html):
    m = OPEN_A_RE.match(tag_html.strip())
    tag = m.group(0) if m else tag_html
    h = HREF_RE.search(tag)
    return (h.group(1) or h.group(2)) if h else None


def lineno(text, pos):
    return text.count("\n", 0, pos) + 1


def site_path(root, p):
    return "/" + p.relative_to(root).as_posix()


# --------------------------------------------------------------------------- discovery
def discover(root, templates, scope, urls_file, hosts):
    pruned = set()
    base = root / scope if scope else root
    for t in templates:
        for p in base.rglob(f"{t}.html"):
            pruned.add(site_path(root, p))
    if urls_file:
        for line in Path(urls_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                n = normalize(line, "/", hosts)
                if n:
                    pruned.add(n)
    return pruned


def load_protected(csv_files, hosts):
    protected = set()
    for f in csv_files or []:
        with open(f, newline="", encoding="utf-8-sig") as fh:
            rows = csv.reader(fh)
            next(rows, None)  # header
            for r in rows:
                if len(r) < 2:
                    continue
                try:
                    clicks = int(r[1])
                except ValueError:
                    continue
                if clicks > 0:
                    n = normalize(r[0], "/", hosts)
                    if n:
                        protected.add(n)
    return protected


def redirect_target(root, path):
    """Nearest ancestor folder that has an index.html (the district hub)."""
    d = posixpath.dirname(path)
    while d and d != "/":
        if (root / d.lstrip("/") / "index.html").exists():
            return d + "/"
        d = posixpath.dirname(d)
    return "/"


# --------------------------------------------------------------------------- editors
def process_html(text, this_path, pruned, hosts, log, rel_file, cta_classes=()):
    def hit(href):
        n = normalize(href, this_path, hosts)
        return n if n in pruned else None

    def cta_pass(s):
        """Remove whole <div class="insight-box">...</div> call-to-action blocks whose links
        all point at pruned pages (balanced-div matching), plus the HTML comment above them."""
        if not cta_classes:
            return s
        cls = "|".join(re.escape(c) for c in cta_classes)
        open_re = re.compile(
            r"(<!--(?:(?!-->).)*-->\s*)?"
            r"(<div\b[^>]*class\s*=\s*[\"'][^\"']*(?<![\w-])(?:%s)(?![\w-])[^\"']*[\"'][^>]*>)" % cls,
            re.I | re.S)
        out, pos = [], 0
        while True:
            m = open_re.search(s, pos)
            if not m:
                break
            depth, end = 1, None
            for t in DIV_TOKEN.finditer(s, m.end(2)):
                depth += -1 if t.group(0).startswith("</") else 1
                if depth == 0:
                    end = t.end()
                    break
            if end is None:
                out.append(s[pos:m.end()])
                pos = m.end()
                continue
            block = s[m.start(2):end]
            hrefs = [get_href(a.group(0)) for a in OPEN_A_RE.finditer(block)]
            targets = [hit(h) for h in hrefs if h]
            if targets and all(targets):
                start = m.start(1) if (m.group(1) and re.search(r"partner|cta", m.group(1), re.I)) else m.start(2)
                end2 = end + re.match(r"[ \t]*(?:\r?\n)?", s[end:]).end()
                out.append(s[pos:start])
                log.append((rel_file, lineno(s, m.start(2)), "removed CTA block", targets[0], ""))
                pos = end2
            else:
                out.append(s[pos:m.end()])
                pos = m.end()
        out.append(s[pos:])
        return "".join(out)

    cur = cta_pass(text)

    def li_cb(m):
        t = hit(get_href(m.group(1)))
        if t:
            log.append((rel_file, lineno(cur, m.start()), "removed <li> link", t, ""))
            return ""
        return m.group(0)

    cur = LI_RE.sub(li_cb, cur)

    def nav_cb(nm):
        nav_start = nm.start()

        def inner(m):
            h = HREF_RE.search(m.group(1))
            t = hit((h.group(1) or h.group(2)) if h else None)
            if t:
                log.append((rel_file, lineno(cur, nav_start + m.start()), "removed nav link", t, ""))
                return ""
            return m.group(0)

        return A_LINE_RE.sub(inner, nm.group(0))

    cur = NAV_RE.sub(nav_cb, cur)

    def card_cb(m):
        # an <a> wrapping block-level content (heading/paragraph/div) is a card: remove all of it
        if not BLOCK_RE.search(m.group(2)):
            return m.group(0)
        h = HREF_RE.search(m.group(1))
        t = hit((h.group(1) or h.group(2)) if h else None)
        if t:
            log.append((rel_file, lineno(cur, m.start()), "removed card link", t, ""))
            return ""
        return m.group(0)

    cur = A_LINE_RE.sub(card_cb, cur)

    def a_cb(m):
        h = HREF_RE.search(m.group(1))
        t = hit((h.group(1) or h.group(2)) if h else None)
        if t:
            ctx = re.sub(r"\s+", " ", cur[max(0, m.start() - 90):m.start()])[-70:]
            log.append((rel_file, lineno(cur, m.start()), "unwrapped link (REVIEW)", t, ctx.strip()))
            return m.group(2)
        return m.group(0)

    cur = A_RE.sub(a_cb, cur)

    def link_cb(m):
        tag = m.group(0)
        if re.search(r"""rel\s*=\s*["']?[^"'>]*alternate""", tag, re.I):
            h = HREF_RE.search(tag)
            t = hit((h.group(1) or h.group(2)) if h else None)
            if t:
                log.append((rel_file, lineno(cur, m.start()), "removed hreflang <link>", t, ""))
                return ""
        return tag

    cur = LINK_RE.sub(link_cb, cur)
    return cur


def process_sitemap(path, pruned, hosts, log, rel_file):
    ET.register_namespace("", SM_NS)
    ET.register_namespace("xhtml", XHTML_NS)
    ET.register_namespace("image", "http://www.google.com/schemas/sitemap-image/1.1")
    ET.register_namespace("news", "http://www.google.com/schemas/sitemap-news/0.9")
    ET.register_namespace("video", "http://www.google.com/schemas/sitemap-video/1.1")
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        print(f"  ! could not parse {rel_file}, skipping", file=sys.stderr)
        return None
    root = tree.getroot()
    changed = False
    for url in list(root.findall(f"{{{SM_NS}}}url")):
        loc = url.find(f"{{{SM_NS}}}loc")
        n = normalize(loc.text if loc is not None else None, "/", hosts)
        if n in pruned:
            root.remove(url)
            log.append((rel_file, 0, "removed sitemap <url>", n, ""))
            changed = True
            continue
        for xl in list(url.findall(f"{{{XHTML_NS}}}link")):
            t = normalize(xl.get("href"), "/", hosts)
            if t in pruned:
                url.remove(xl)
                log.append((rel_file, 0, "removed sitemap hreflang", t, ""))
                changed = True
    if not changed:
        return None
    ET.indent(tree, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="site folder containing the final .html files")
    ap.add_argument("--templates", nargs="+", default=DEFAULT_TEMPLATES,
                    help="page file names (without .html) to prune, default: %(default)s")
    ap.add_argument("--scope", default="districts", help="subfolder to search for templates (default: districts)")
    ap.add_argument("--urls-file", help="text file of extra URLs/paths to prune, one per line")
    ap.add_argument("--protect-csv", nargs="*", help="GSC Pages exports; pages with clicks > 0 are never pruned")
    ap.add_argument("--cta-classes", nargs="*", default=DEFAULT_CTA_CLASSES,
                    help="CSS classes of call-to-action boxes to delete whole when all their links are pruned (default: %(default)s)")
    ap.add_argument("--hosts", nargs="+", default=DEFAULT_HOSTS, help="hostnames treated as internal")
    ap.add_argument("--out", default="prune_report", help="folder for reports/redirect files")
    ap.add_argument("--apply", action="store_true", help="actually change files (default is dry run)")
    ap.add_argument("--no-backup", action="store_true", help="skip backing up changed/deleted files")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        sys.exit(f"--root {root} is not a folder")
    hosts = {h.lower() for h in args.hosts}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    pruned = discover(root, args.templates, args.scope, args.urls_file, hosts)
    protected = load_protected(args.protect_csv, hosts)
    skipped = sorted(pruned & protected)
    pruned -= protected
    # only keep pages that actually exist on disk (extra URLs may not)
    missing = sorted(p for p in pruned if not (root / p.lstrip("/")).exists())
    pruned -= set(missing)

    print(f"Mode: {'APPLY' if args.apply else 'DRY RUN'}   root: {root}")
    print(f"Pages to prune: {len(pruned)}   protected (had clicks): {len(skipped)}   not found on disk: {len(missing)}")
    for s in skipped:
        print(f"  protected: {s}")
    if not pruned:
        return

    log = []            # (file, line, action, target)
    new_content = {}    # Path -> new text
    scanned = {}        # Path -> text used for remaining-reference scan

    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTS]
    pruned_files = {root / p.lstrip("/") for p in pruned}
    for f in files:
        if f in pruned_files or out.resolve() in f.parents:
            continue
        rel = f.relative_to(root).as_posix()
        try:
            with open(f, encoding="utf-8", newline="") as fh:
                text = fh.read()
        except UnicodeDecodeError:
            print(f"  ! skipping non-UTF-8 file {rel}", file=sys.stderr)
            continue
        new = None
        if f.suffix.lower() in HTML_EXTS:
            res = process_html(text, "/" + rel, pruned, hosts, log, rel, args.cta_classes)
            new = res if res != text else None
        elif f.name.lower().startswith("sitemap") and f.suffix.lower() == ".xml":
            new = process_sitemap(f, pruned, hosts, log, rel)
        if new is not None:
            new_content[f] = new
        scanned[f] = new if new is not None else text

    # redirects
    redirects = sorted((p, redirect_target(root, p)) for p in pruned)

    # remaining references (absolute path substrings; catches JSON-LD, json data, llms.txt, ...)
    pat = re.compile("|".join(re.escape(p) for p in sorted(pruned, key=len, reverse=True)))
    remaining = []
    for f, text in scanned.items():
        for m in pat.finditer(text):
            remaining.append((f.relative_to(root).as_posix(), lineno(text, m.start()), m.group(0)))

    # ---- reports
    with open(out / "changes.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "line", "action", "target_page", "context"])
        w.writerows(log)
        for p in sorted(pruned):
            w.writerow([p.lstrip("/"), "", "deleted page", p, ""])
    with open(out / "redirects.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["from", "to", "status"])
        w.writerows([(a, b, 301) for a, b in redirects])
    (out / "redirects_netlify_cloudflare.txt").write_text(
        "\n".join(f"{a} {b} 301" for a, b in redirects) + "\n", encoding="utf-8")
    (out / "redirects_apache.htaccess").write_text(
        "\n".join(f"Redirect 301 {a} {b}" for a, b in redirects) + "\n", encoding="utf-8")
    with open(out / "remaining_references.txt", "w", encoding="utf-8") as fh:
        for rel, ln, tgt in remaining:
            fh.write(f"{rel}:{ln}  {tgt}\n")

    # ---- apply
    if args.apply:
        backup = None
        if not args.no_backup:
            backup = root.parent / f"_pruned_backup_{datetime.now():%Y%m%d_%H%M%S}"
        def stash(p):
            if backup:
                dest = backup / p.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
        for f, text in new_content.items():
            stash(f)
            with open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
        for p in pruned_files:
            stash(p)
            p.unlink()
        # remove folders emptied by the deletions
        for p in pruned_files:
            d = p.parent
            while d != root and d.exists() and not any(d.iterdir()):
                d.rmdir()
                d = d.parent
        if backup:
            print(f"Backup of changed/deleted files: {backup}")

    # ---- summary
    by_action = {}
    for _, _, a, *_rest in log:
        by_action[a] = by_action.get(a, 0) + 1
    print("\nSummary")
    print(f"  pages {'deleted' if args.apply else 'to delete'}: {len(pruned)}")
    for a, n in sorted(by_action.items()):
        print(f"  {a}: {n}")
    print(f"  files {'modified' if args.apply else 'to modify'}: {len(new_content)}")
    print(f"  remaining references needing manual review: {len(remaining)}")
    print(f"\nReports in {out}/ :")
    print("  changes.csv, redirects.csv, redirects_netlify_cloudflare.txt, redirects_apache.htaccess,")
    print("  remaining_references.txt")
    review = [r for r in log if "REVIEW" in r[2]]
    if review:
        print(f"\n{len(review)} links were unwrapped to plain text instead of removed - check these for leftover labels:")
        for f, ln, a, t, ctx in review[:15]:
            print(f"  {f}:{ln} -> {t}   ...{ctx}")
        if len(review) > 15:
            print(f"  ... {len(review) - 15} more in changes.csv")
    if not args.apply:
        print("\nDry run only - nothing was changed. Re-run with --apply to make the changes.")
    print("\nAfter deploying: add the redirect rules to your host, resubmit the sitemap, "
          "and confirm the old URLs 301 to the hub.")


if __name__ == "__main__":
    main()