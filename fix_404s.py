#!/usr/bin/env python3
"""
fix_404s.py - clean up the 404s in a Site Audit export by editing the site's source files.

What it does (dry run by default, nothing is written without --apply):
  * <link rel="canonical" href="BROKEN">   -> repointed to the page's own URL (self-canonical)
  * <link rel="alternate" ... href="BROKEN"> (hreflang) -> repointed if a replacement is found,
                                              otherwise the tag is removed
  * <a href="BROKEN">                      -> repointed if a replacement is found; otherwise
                                              reported (or unwrapped with --unwrap)
  * sitemap.xml <url> blocks for broken URLs are removed

A replacement is found from, in order:
  1. an explicit --map OLD_PATH=NEW_PATH
  2. a single file elsewhere in the repo with the same file name as the broken URL

Usage:
  python fix_404s.py --csv 404s.csv --root /path/to/nyspecialed            # preview
  python fix_404s.py --csv 404s.csv --root /path/to/nyspecialed --apply    # write changes
  python fix_404s.py --csv 404s.csv --root . --apply \
      --map /districts/evaluation-process.html=/evaluation-process.html \
      --map /districts/parent-advocacy-guide.html=/parent-advocacy-guide.html

Review the result with `git diff` before committing.
"""
import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}

LINK_RE = re.compile(r"([ \t]*)(<link\b[^>]*>)([ \t]*\r?\n)?", re.I)
A_OPEN_RE = re.compile(r"<a\b[^>]*>", re.I)
A_FULL_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.I | re.S)


def attr_re(name):
    return re.compile(r"(\b%s\s*=\s*)([\"'])(.*?)\2" % name, re.I | re.S)


def get_attr(tag, name):
    m = attr_re(name).search(tag)
    return m.group(3) if m else None


def set_attr(tag, name, value):
    return attr_re(name).sub(
        lambda m: f"{m.group(1)}{m.group(2)}{value}{m.group(2)}", tag, count=1
    )


def url_key(path):
    """Normalise a URL path so /a/b.html, /a/b and /a/b/ compare equal."""
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    if path.endswith(".html"):
        path = path[:-5]
    return path.rstrip("/") or "/"


class Fixer:
    def __init__(self, root, host, scheme, broken_paths, mapping, exts, unwrap):
        self.root = root
        self.host = host  # e.g. www.newyorkspecialed.net
        self.bare_host = host.removeprefix("www.")
        self.scheme = scheme
        self.broken = {url_key(p): p for p in broken_paths}
        self.mapping = {url_key(k): v for k, v in mapping.items()}
        self.exts = exts
        self.unwrap = unwrap
        self.files = [
            p for p in root.rglob("*")
            if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_DIRS)
        ]
        self.by_name = {}
        for p in self.files:
            self.by_name.setdefault(p.name, []).append(p)
        self.log = Counter()
        self.unresolved = []

    # ---- URL helpers -------------------------------------------------
    def page_url(self, f):
        return f"{self.scheme}://{self.host}/" + f.relative_to(self.root).as_posix()

    def broken_path_for(self, href, page_url):
        """Return the broken URL path this href points to, or None."""
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return None
        u = urlparse(urljoin(page_url, href))
        if u.netloc.removeprefix("www.") != self.bare_host:
            return None
        key = url_key(u.path)
        return self.broken.get(key) and key

    def replacement_for(self, broken_key):
        if broken_key in self.mapping:
            return self.mapping[broken_key]
        name = Path(self.broken[broken_key]).name
        candidates = [
            "/" + p.relative_to(self.root).as_posix()
            for p in self.by_name.get(name, [])
            if url_key("/" + p.relative_to(self.root).as_posix()) != broken_key
        ]
        return candidates[0] if len(candidates) == 1 else None

    # ---- per-file edits ----------------------------------------------
    def fix_html(self, f, text):
        page_url = self.page_url(f)
        rel = f.relative_to(self.root).as_posix()

        def link_sub(m):
            indent, tag, nl = m.group(1), m.group(2), m.group(3) or ""
            href = get_attr(tag, "href")
            key = self.broken_path_for(href, page_url)
            if not key:
                return m.group(0)
            rels = (get_attr(tag, "rel") or "").lower().split()
            if "canonical" in rels:
                self.log["canonical -> self"] += 1
                return indent + set_attr(tag, "href", page_url) + nl
            if "alternate" in rels:
                new = self.replacement_for(key)
                if new:
                    self.log["alternate repointed"] += 1
                    return indent + set_attr(tag, "href", f"{self.scheme}://{self.host}{new}") + nl
                self.log["alternate removed"] += 1
                return ""
            self.unresolved.append((rel, href, "<link> with other rel"))
            return m.group(0)

        text = LINK_RE.sub(link_sub, text)

        def a_sub(m):
            attrs, inner = m.group(1), m.group(2)
            href = get_attr("<a " + attrs + ">", "href")
            key = self.broken_path_for(href, page_url)
            if not key:
                return m.group(0)
            new = self.replacement_for(key)
            if new:
                self.log["anchor repointed"] += 1
                if href.lower().startswith("http"):
                    new = f"{self.scheme}://{self.host}{new}"
                return f"<a {set_attr(attrs, 'href', new).strip()}>{inner}</a>"
            if self.unwrap:
                self.log["anchor unwrapped"] += 1
                return inner
            self.unresolved.append((rel, href, "anchor - no replacement (use --map or --unwrap)"))
            return m.group(0)

        return A_FULL_RE.sub(a_sub, text)

    def fix_sitemap(self, f, text):
        def url_sub(m):
            loc = re.search(r"<loc>\s*(.*?)\s*</loc>", m.group(0), re.S)
            if loc and self.broken_path_for(loc.group(1), f"{self.scheme}://{self.host}/"):
                self.log["sitemap entry removed"] += 1
                return ""
            return m.group(0)

        return re.sub(r"[ \t]*<url>.*?</url>[ \t]*\r?\n?", url_sub, text, flags=re.S)

    def run(self, apply):
        changed = []
        for f in self.files:
            is_sitemap = f.name.startswith("sitemap") and f.suffix == ".xml"
            if f.suffix.lower() not in self.exts and not is_sitemap:
                continue
            try:
                with open(f, encoding="utf-8", newline="") as fh:
                    old = fh.read()
            except UnicodeDecodeError:
                continue
            new = self.fix_sitemap(f, old) if is_sitemap else self.fix_html(f, old)
            if new != old:
                changed.append(f)
                if apply:
                    with open(f, "w", encoding="utf-8", newline="") as fh:
                        fh.write(new)
        return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True, help="404 export (needs a 'URL' column)")
    ap.add_argument("--root", required=True, help="site root folder (where / maps to)")
    ap.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    ap.add_argument("--map", action="append", default=[], metavar="OLD=NEW",
                    help="explicit replacement path, e.g. /districts/x.html=/x.html (repeatable)")
    ap.add_argument("--unwrap", action="store_true",
                    help="for <a> links with no replacement, remove the link but keep its text")
    ap.add_argument("--ext", default=".html,.htm", help="file extensions to edit (comma separated)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        sys.exit(f"Root folder not found: {root}")

    with open(args.csv, encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("URL")]
    urls = [r["URL"].strip() for r in rows if str(r.get("HTTP status code", "404")).strip().startswith("4")]
    if not urls:
        sys.exit("No 4xx URLs found in the CSV.")
    first = urlparse(urls[0])
    broken_paths = [urlparse(u).path for u in urls]

    mapping = {}
    for item in args.map:
        old, _, new = item.partition("=")
        if not new:
            sys.exit(f"--map needs OLD=NEW, got: {item}")
        mapping[old] = new

    exts = {e.strip().lower() if e.strip().startswith(".") else "." + e.strip().lower()
            for e in args.ext.split(",")}
    fx = Fixer(root, first.netloc, first.scheme, broken_paths, mapping, exts, args.unwrap)
    changed = fx.run(args.apply)

    print(f"{'APPLIED' if args.apply else 'DRY RUN'}: {len(broken_paths)} broken URLs, "
          f"{len(changed)} files {'changed' if args.apply else 'would change'}")
    for action, n in sorted(fx.log.items()):
        print(f"  {n:4d}  {action}")
    if fx.unresolved:
        print(f"\n{len(fx.unresolved)} link(s) still need a decision:")
        for rel, href, why in fx.unresolved:
            print(f"  {rel}: {href}  [{why}]")
    if not changed:
        print("\nNothing matched. Check --root points at the folder that serves '/', "
              "and that these pages are plain .html files (not generated at build time).")
    elif not args.apply:
        print("\nRe-run with --apply to write these changes.")


if __name__ == "__main__":
    main()