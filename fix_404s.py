#!/usr/bin/env python3
"""
fix_404s.py - fix the broken (404) URLs from a site-crawl export and clean the references to them.

Reads the crawl CSV (columns used: URL, First found at, HTTP status code) and, for every 404,
applies one of these fixes by rule:

  remove     /districts/<slug>/<template>.html where the page was pruned (default templates:
             partners, what-is-an-iep).  The dangling links / hreflang alternates are removed
             using the same logic as prune_pages.py, and a 301 to the district hub is written
             to the redirect files.

  self       /guides/post-N-<slug>-es/   and   /es/guias/<slug>-es/   (old Spanish URLs)
             The page that "found" the URL is the Spanish page itself, so the reference is a
             self-reference (canonical / og:url / hreflang / JSON-LD).  It is rewritten to the
             page's real URL.  References inside ordinary <a> links are NOT guessed - they are
             reported for manual review.

  replace    /guides/post-N-<slug>/  (old English URL) -> /guides/<slug>.html   (must exist)
             /es/guias/              -> /guides/es/                              (must exist)
             Replaced everywhere on the site.

  absolutize /districts/<name>.html found on a slashless hub URL such as /districts/<slug>
             (no trailing slash).  The hub's relative links resolve one folder too high.  The
             relative href/src values in that page are rewritten to root-relative paths.

Also (on by default):
  * internal links to folder pages without a trailing slash (/districts/<slug>) get the slash,
    so pages are not reached at the slashless URL again.  Disable with --no-slash-fix.
  * sitemap*.xml entries for the 404 URLs are removed.

DRY RUN by default; add --apply to write changes.  Line endings are preserved and a backup of
every changed file is kept.  Put this file next to prune_pages.py (it re-uses its link cleaner).

Usage
-----
  python fix_404s.py --root . --crawl "Newyorkspecialed_29-Oct-2026_404_page_-_Sheet1.csv"
  python fix_404s.py --root . --crawl 404s.csv --apply
"""
import argparse
import csv
import posixpath
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    import prune_pages as pp
except ImportError:
    sys.exit("fix_404s.py must sit in the same folder as prune_pages.py")

DEFAULT_TEMPLATES = ["partners", "what-is-an-iep"]
DEFAULT_HOSTS = ["www.newyorkspecialed.net", "newyorkspecialed.net"]
HTML_EXTS = {".html", ".htm", ".xhtml"}
SKIP_DIRS = {".git", "node_modules", "prune_report", "fix_404_report"}
ATTR_RE = re.compile(r"""(\b(?:href|src)\s*=\s*)(["'])(.*?)\2""", re.I)
HREF_ONLY_RE = re.compile(r"""(\bhref\s*=\s*)(["'])(.*?)\2""", re.I)


# ----------------------------------------------------------------------------- helpers
def url_to_file(root, path):
    p = path.lstrip("/")
    c = root / p
    if p and c.is_file():
        return c
    if (c / "index.html").is_file():
        return c / "index.html"
    if p and (root / (p + ".html")).is_file():
        return root / (p + ".html")
    return None


def occ_regex(path, hosts):
    """Match an absolute (our hosts) or root-relative reference to `path`, with or without a
    trailing slash, but never a longer path that merely starts with it."""
    host_alt = "|".join(re.escape(h) for h in sorted(hosts, key=len, reverse=True))
    return re.compile(
        r"(?:(?P<host>https?://(?:%s))|(?<![\w\-./:]))%s(?:/(?![\w\-.%%~]))?(?![\w\-.%%~/])"
        % (host_alt, re.escape(path)),
        re.I,
    )


def ctx_kind(text, pos):
    """What kind of markup is `pos` inside: head (<link>/<meta>), jsonld, anchor, text, other."""
    i = text.rfind("<", 0, pos)
    if i == -1:
        return "other"
    m = re.match(r"<\s*([a-zA-Z0-9]+)", text[i:i + 40])
    tag = m.group(1).lower() if m else ""
    if tag == "script":
        close = text.find(">", i)
        return "jsonld" if "ld+json" in text[i:close if close != -1 else i + 200].lower() else "other"
    if ">" in text[i:pos]:
        return "text"
    return {"link": "head", "meta": "head", "a": "anchor"}.get(tag, "other")


def snippet(text, pos, width=70):
    return re.sub(r"\s+", " ", text[max(0, pos - width):pos + width]).strip()


def lineno(text, pos):
    return text.count("\n", 0, pos) + 1


# ----------------------------------------------------------------------------- classify
def classify(bad, src_url, src_path, root, templates, es_index):
    """Return dict(kind, new, scope) or dict(kind='manual', why=...)."""
    src_file = url_to_file(root, src_path) if src_path else None
    slashless_folder = bool(
        src_file and src_file.name == "index.html" and not urlparse(src_url).path.endswith("/")
        and src_path not in ("", "/")
    )
    name = posixpath.basename(bad)
    stem = name[:-5] if name.endswith(".html") else name

    # 1) relative link resolved against a slashless folder URL
    if slashless_folder and posixpath.dirname(bad) == posixpath.dirname(src_path):
        return {"kind": "absolutize", "src": src_path}

    # 2) pages we pruned
    if bad.startswith("/districts/") and name.endswith(".html") and stem in templates:
        if (root / bad.lstrip("/")).exists():
            return {"kind": "manual", "why": "file still exists on disk - is the site deployed/rebuilt?"}
        return {"kind": "remove"}

    # 3) old post-N URLs and old /es/guias/ URLs
    m = re.match(r"^/guides/post-\d+-(.+)$", bad)
    m2 = re.match(r"^/es/guias/(.+)$", bad)
    slug_full = (m or m2).group(1) if (m or m2) else None
    if slug_full:
        is_es = slug_full.endswith("-es")
        slug = slug_full[:-3] if is_es else slug_full
        if m and not is_es:
            cand = f"/guides/{slug}.html"
            if src_path == cand or (root / cand.lstrip("/")).is_file():
                return {"kind": "replace", "new": cand, "scope": "all"}
            return {"kind": "manual", "why": f"{cand} does not exist"}
        if src_file and src_path.endswith(".html") and "/guides/es/" in src_path:
            return {"kind": "self", "new": src_path, "src": src_path}
        return {"kind": "manual", "why": "could not match to a Spanish guide"}

    # 4) Spanish guides index
    if bad == "/es/guias":
        idx = es_index or ("/guides/es/" if (root / "guides/es/index.html").is_file() else None)
        if idx:
            return {"kind": "replace", "new": idx, "scope": "all"}
        return {"kind": "manual", "why": "no Spanish guides index found (use --es-index)"}

    return {"kind": "manual", "why": "no rule for this pattern"}


# ----------------------------------------------------------------------------- rewriters
def apply_replacements(text, file_path, rules, hosts, log, rel):
    for r in rules:
        if r["kind"] == "self" and r["src"] != file_path:
            continue
        rx = occ_regex(r["bad"], hosts)
        allowed = ("head", "jsonld") if r["kind"] == "self" else None
        out, pos = [], 0
        for m in rx.finditer(text):
            kind = ctx_kind(text, m.start())
            if allowed and kind not in allowed:
                continue  # leave it; the leftover scan will report it
            out.append(text[pos:m.start()])
            out.append((m.group("host") or "") + r["new"])
            log.append((rel, lineno(text, m.start()), f"replaced ({r['kind']}, in {kind})", r["bad"], r["new"]))
            pos = m.end()
        out.append(text[pos:])
        text = "".join(out)
    return text


def absolutize(text, file_path, log, rel):
    """Rewrite relative href/src values to root-relative (only meaningful for index.html pages)."""
    base = posixpath.dirname(file_path) + "/"

    def fix(m):
        v = m.group(3).strip()
        if not v or v.startswith(("#", "/", "mailto:", "tel:", "javascript:", "data:")) \
                or re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", v):
            return m.group(0)
        u = urlparse(v)
        if not u.path:
            return m.group(0)
        new = posixpath.normpath(posixpath.join(base, u.path))
        if u.path.endswith("/") and not new.endswith("/"):
            new += "/"
        if u.query:
            new += "?" + u.query
        if u.fragment:
            new += "#" + u.fragment
        log.append((rel, lineno(text, m.start()), "made root-relative", v, new))
        return f"{m.group(1)}{m.group(2)}{new}{m.group(2)}"

    return ATTR_RE.sub(fix, text)


def add_slashes(text, root, hosts, log, rel):
    """href to a folder page (has index.html) without trailing slash -> add the slash."""
    def fix(m):
        v = m.group(3)
        u = urlparse(v)
        if u.scheme in ("http", "https"):
            if u.netloc.lower() not in hosts:
                return m.group(0)
        elif u.scheme or not v.startswith("/"):
            return m.group(0)
        p = u.path
        if not p or p.endswith("/") or posixpath.splitext(p)[1]:
            return m.group(0)
        if not (root / unquote(p).lstrip("/") / "index.html").is_file():
            return m.group(0)
        new = v[: v.index(p) + len(p)] + "/" + v[v.index(p) + len(p):]
        log.append((rel, lineno(text, m.start()), "added trailing slash", v, new))
        return f"{m.group(1)}{m.group(2)}{new}{m.group(2)}"

    return HREF_ONLY_RE.sub(fix, text)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="site folder with the final .html files")
    ap.add_argument("--crawl", required=True, help="crawl export CSV listing the 404s")
    ap.add_argument("--templates", nargs="+", default=DEFAULT_TEMPLATES,
                    help="pruned page names whose dangling links are removed (default: %(default)s)")
    ap.add_argument("--es-index", help="path of the Spanish guides index, e.g. /guides/es/")
    ap.add_argument("--absolutize-all-index", action="store_true",
                    help="make relative links root-relative on EVERY non-root index.html, not only the flagged hubs")
    ap.add_argument("--no-slash-fix", action="store_true", help="do not add trailing slashes to folder links")
    ap.add_argument("--hosts", nargs="+", default=DEFAULT_HOSTS)
    ap.add_argument("--out", default="fix_404_report")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    hosts = {h.lower() for h in args.hosts}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # ---- read the crawl
    rows = []
    with open(args.crawl, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if str(r.get("HTTP status code", "404")).strip() not in ("404", "410"):
                continue
            bad = pp.normalize(r["URL"], "/", hosts)
            if not bad:
                continue
            src_url = r.get("First found at", "")
            rows.append((bad, src_url, pp.normalize(src_url, "/", hosts)))
    print(f"Mode: {'APPLY' if args.apply else 'DRY RUN'}   root: {root}   404 rows: {len(rows)}")

    # ---- classify
    rules, manual = [], []
    remove_set, absolutize_files = set(), set()
    for bad, src_url, src_path in rows:
        c = classify(bad, src_url, src_path, root, set(args.templates), args.es_index)
        c["bad"] = bad
        if c["kind"] == "manual":
            manual.append((bad, src_path, c["why"]))
        elif c["kind"] == "remove":
            remove_set.add(bad)
            rules.append(c)
        elif c["kind"] == "absolutize":
            f = url_to_file(root, c["src"])
            absolutize_files.add("/" + f.relative_to(root).as_posix())
            rules.append(c)
        else:
            rules.append(c)
    counts = {}
    for r in rules:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    print("Plan:", ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())), f"| manual: {len(manual)}")

    replace_rules = [r for r in rules if r["kind"] in ("self", "replace")]

    # ---- process files
    log, new_content, scanned = [], {}, {}
    files = [p for p in root.rglob("*") if p.is_file()
             and not (SKIP_DIRS & set(p.relative_to(root).parts))
             and (p.suffix.lower() in HTML_EXTS or (p.name.lower().startswith("sitemap") and p.suffix.lower() == ".xml"))]
    for f in files:
        rel = f.relative_to(root).as_posix()
        fpath = "/" + rel
        try:
            with open(f, encoding="utf-8", newline="") as fh:
                text = fh.read()
        except UnicodeDecodeError:
            print(f"  ! skipping non-UTF-8 file {rel}", file=sys.stderr)
            continue
        orig = text
        if f.suffix.lower() == ".xml":
            bad_all = {r["bad"] for r in rules if r["kind"] != "absolutize"}
            res = pp.process_sitemap(f, bad_all, hosts, log, rel)
            if res is not None:
                text = res
        else:
            if remove_set:
                text = _prune_with_log(text, fpath, remove_set, hosts, log, rel)
            text = apply_replacements(text, fpath, replace_rules, hosts, log, rel)
            is_nonroot_index = f.name == "index.html" and fpath != "/index.html"
            if fpath in absolutize_files or (args.absolutize_all_index and is_nonroot_index):
                text = absolutize(text, fpath, log, rel)
            if not args.no_slash_fix:
                text = add_slashes(text, root, hosts, log, rel)
        if text != orig:
            new_content[f] = text
        scanned[f] = text

    # ---- leftovers: anything still pointing at a 404 URL
    leftovers = []
    for r in rules:
        if r["kind"] == "absolutize":
            continue
        rx = occ_regex(r["bad"], hosts)
        for f, text in scanned.items():
            if f.suffix.lower() not in HTML_EXTS:
                continue
            for m in rx.finditer(text):
                leftovers.append((f.relative_to(root).as_posix(), lineno(text, m.start()),
                                  ctx_kind(text, m.start()), r["bad"], snippet(text, m.start())))

    # ---- redirects for the old URLs
    redirects = []
    for r in rules:
        if r["kind"] in ("self", "replace"):
            redirects.append((r["bad"] + "/" if r["bad"].startswith(("/guides/post-", "/es/guias")) else r["bad"], r["new"]))
        elif r["kind"] == "remove":
            redirects.append((r["bad"], pp.redirect_target(root, r["bad"])))
    redirects = sorted(set(redirects))

    # ---- reports
    with open(out / "changes.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "line", "action", "from", "to_or_context"])
        w.writerows(log)
    with open(out / "needs_manual_review.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "line", "kind", "url", "context"])
        for b, s, why in manual:
            w.writerow([s or "", "", "no automatic fix: " + why, b, ""])
        w.writerows(leftovers)
    (out / "redirects_netlify_cloudflare.txt").write_text(
        "\n".join(f"{a} {b} 301" for a, b in redirects) + "\n", encoding="utf-8")
    (out / "redirects_apache.htaccess").write_text(
        "\n".join(f"Redirect 301 {a} {b}" for a, b in redirects) + "\n", encoding="utf-8")

    # ---- apply
    if args.apply:
        backup = None if args.no_backup else root.parent / f"_fix404_backup_{datetime.now():%Y%m%d_%H%M%S}"
        for f, text in new_content.items():
            if backup:
                dest = backup / f.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
            with open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
        if backup:
            print(f"Backup of changed files: {backup}")

    # ---- summary
    by = {}
    for _, _, a, _, _ in log:
        a = re.sub(r" \(.*\)", "", a)
        by[a] = by.get(a, 0) + 1
    print("\nSummary")
    for a, n in sorted(by.items()):
        print(f"  {a}: {n}")
    print(f"  files {'modified' if args.apply else 'to modify'}: {len(new_content)}")
    print(f"  404s with no automatic fix: {len(manual)}")
    print(f"  references still pointing at a 404 URL: {len(leftovers)}")
    for b, s, why in manual[:10]:
        print(f"    manual: {b}  (found at {s}) - {why}")
    for rel, ln, k, b, sn in leftovers[:10]:
        print(f"    left:   {rel}:{ln} [{k}] {b}  ...{sn}")
    print(f"\nReports in {out}/: changes.csv, needs_manual_review.csv, redirects_*.txt/.htaccess")
    if not args.apply:
        print("\nDry run only - nothing was changed. Re-run with --apply to write the changes.")
    print("\nAfter deploying: add the redirect rules, re-crawl, and resubmit the sitemap.")
    print("Tip: if https://<site>/guides (no slash) returns 200 instead of redirecting to /guides/, "
          "enable trailing-slash redirects on your host so relative links can't break again.")


def _prune_with_log(text, fpath, remove_set, hosts, log, rel):
    """Run prune_pages' link cleaner and translate its log rows to this script's 5-column format."""
    tmp = []
    new = pp.process_html(text, fpath, remove_set, hosts, tmp, rel, pp.DEFAULT_CTA_CLASSES)
    for f, ln, action, target, ctx in tmp:
        log.append((f, ln, action + " (pruned page)", target, ctx))
    return new


if __name__ == "__main__":
    main()