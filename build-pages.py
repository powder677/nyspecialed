#!/usr/bin/env python3
"""
NY Special Ed — Guide Builder
==============================
Converts Markdown guide files into finished HTML pages by injecting
content into guide-template.html (English) or guide-template-es.html (Spanish).

Usage:
    python build_guides.py

Folder layout expected (edit GUIDES_DIR at the top to match your machine):
    guides/
    ├── guide-template.html          ← English template
    ├── some-guide.md
    ├── another-guide.md
    └── es/
        ├── guide-template-es.html   ← Spanish template
        ├── alguna-guia.md
        └── otra-guia.md

Output:
    Each .md file produces a matching .html file in the same folder.
    e.g.  guides/cse-meeting-guide.md  →  guides/cse-meeting-guide.html
          guides/es/guia-cse.md        →  guides/es/guia-cse.html

Optional YAML front-matter at the top of any .md file:
    ---
    title: Your Post Title Here
    description: 150-char SEO description.
    category: CSE Process
    date: January 1, 2026
    read_time: 8 min read
    slug: your-post-slug          <- overrides filename-derived slug
    en_slug: english-version-slug <- (ES only) links the language banner
    ---

    If no front-matter, the script uses the first # H1 as the title and
    derives everything else automatically from the filename / word count.
"""

import os
import re
import sys
import copy
from pathlib import Path
from datetime import date

# ── Third-party (pip install markdown beautifulsoup4 python-slugify) ──────────
try:
    import markdown
    from bs4 import BeautifulSoup, NavigableString, Tag
    from slugify import slugify
except ImportError:
    sys.exit(
        "Missing dependencies. Run:\n"
        "  pip install markdown beautifulsoup4 python-slugify"
    )

# =============================================================================
# ✏️  CONFIGURATION — edit GUIDES_DIR to match your machine
# =============================================================================
GUIDES_DIR = Path(r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\guides")
BASE_URL   = "https://www.newyorkspecialed.net"
# =============================================================================

ES_DIR       = GUIDES_DIR / "es"
EN_TEMPLATE  = GUIDES_DIR / "guide-template.html"
ES_TEMPLATE  = ES_DIR     / "guide-template-es.html"

MD_EXTENSIONS = [
    "markdown.extensions.extra",   # tables, fenced code, footnotes, attr_list
    "markdown.extensions.toc",     # auto-ids on headings
    "markdown.extensions.smarty",  # curly quotes / em-dashes
]


# =============================================================================
# HELPERS
# =============================================================================

def parse_frontmatter(text: str) -> tuple:
    """
    Extract optional YAML-style front-matter block from markdown.
    Returns (meta_dict, remaining_markdown).
    Handles simple key: value pairs only (no nested structures).
    """
    meta = {}
    if not text.lstrip().startswith("---"):
        return meta, text

    first_dash = text.index("---")
    search_start = first_dash + 3
    end = text.find("---", search_start)
    if end == -1:
        return meta, text

    fm_block = text[search_start:end].strip()
    body     = text[end + 3:].lstrip("\n")

    for line in fm_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip().lower()] = val.strip()

    return meta, body


def extract_h1(md_text: str) -> tuple:
    """
    Pull the first # Heading from markdown text.
    Returns (title_string_or_None, md_without_h1).
    """
    lines = md_text.splitlines()
    title = None
    rest  = []
    found = False
    for line in lines:
        if not found and re.match(r"^#\s+", line):
            title = re.sub(r"^#\s+", "", line).strip()
            found = True
        else:
            rest.append(line)
    return title, "\n".join(rest)


def md_to_html(md_text: str) -> str:
    """Convert markdown string to HTML string."""
    return markdown.markdown(md_text, extensions=MD_EXTENSIONS)


def build_toc(html_body: str) -> list:
    """
    Return list of {id, text} dicts for every <h2> in the HTML body.
    Used to populate the sidebar Table of Contents.
    """
    soup    = BeautifulSoup(html_body, "html.parser")
    entries = []
    for h2 in soup.find_all("h2"):
        heading_id   = h2.get("id") or slugify(h2.get_text())
        heading_text = h2.get_text()
        entries.append({"id": heading_id, "text": heading_text})
    return entries


def estimate_read_time(text: str, lang: str = "en") -> str:
    minutes = max(1, round(len(text.split()) / 200))
    if lang == "es":
        return f"{minutes} min de lectura"
    return f"{minutes} min read"


def today_formatted(lang: str = "en") -> str:
    d = date.today()
    if lang == "es":
        months = ["enero","febrero","marzo","abril","mayo","junio",
                  "julio","agosto","septiembre","octubre","noviembre","diciembre"]
        return f"{d.day} de {months[d.month - 1]} de {d.year}"
    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    return f"{months[d.month - 1]} {d.day}, {d.year}"


def safe_copy(tag):
    """BeautifulSoup deep-copy helper that works across BS4 versions."""
    return copy.copy(tag)


# =============================================================================
# TEMPLATE INJECTION
# =============================================================================

def inject(soup: BeautifulSoup, meta: dict, title: str,
           html_body: str, toc_entries: list, slug: str, lang: str) -> None:
    """
    Mutates `soup` in-place, replacing all template placeholders with real
    content.  Works for both English (lang='en') and Spanish (lang='es').
    """
    is_es      = (lang == "es")
    path_seg   = "es/guias" if is_es else "guides"
    canon_url  = f"{BASE_URL}/{path_seg}/{slug}/"
    page_title = f"{title} | NY Special Ed"

    default_desc = (
        f"Aprenda sobre {title}. Una guía en español para padres de Nueva York."
        if is_es else
        f"Learn about {title}. A plain-language guide for New York parents navigating special education."
    )
    desc      = meta.get("description", default_desc)[:160]
    category  = meta.get("category", "Proceso CSE" if is_es else "CSE Process")
    post_date = meta.get("date", today_formatted(lang))
    read_time = meta.get("read_time", estimate_read_time(html_body, lang))

    # ── <title> ───────────────────────────────────────────────────────────────
    title_tag = soup.find("title")
    if title_tag:
        title_tag.string = page_title

    # ── <meta> tags ───────────────────────────────────────────────────────────
    meta_map = {
        "description":       desc,
        "og:title":          page_title,
        "og:description":    desc,
        "og:url":            canon_url,
        "twitter:title":     page_title,
        "twitter:description": desc,
    }
    for m in soup.find_all("meta"):
        key = m.get("name") or m.get("property") or ""
        if key in meta_map:
            m["content"] = meta_map[key]

    # ── <link rel="canonical"> ────────────────────────────────────────────────
    canon_tag = soup.find("link", rel="canonical")
    if canon_tag:
        canon_tag["href"] = canon_url

    # ── Language switcher (ES only) ───────────────────────────────────────────
    if is_es:
        en_slug   = meta.get("en_slug", slug)
        lang_link = soup.select_one(".lang-banner a")
        if lang_link:
            lang_link["href"] = f"{BASE_URL}/guides/{en_slug}/"

    # ── Breadcrumb last item ──────────────────────────────────────────────────
    # Looks for a bare NavigableString in the breadcrumb nav that matches
    # the template placeholder text.
    breadcrumb_nav = soup.find("nav", {"aria-label": re.compile(r"[Rr]uta|[Bb]read")})
    if breadcrumb_nav:
        for node in breadcrumb_nav.find_all(string=True):
            clean = node.strip()
            if clean in ("POST TITLE SHORT", "TÍTULO CORTO DEL ARTÍCULO"):
                node.replace_with(title[:60])
                break

    # ── Category badge ────────────────────────────────────────────────────────
    badge = soup.find(class_="blog-category-badge")
    if badge:
        badge.clear()
        if is_es:
            badge.append(BeautifulSoup(f"&#127466;&#127480; {category}", "html.parser"))
        else:
            badge.string = category

    # ── Hero <h1> ─────────────────────────────────────────────────────────────
    hero_h1 = soup.find("h1", class_="blog-hero-title")
    if hero_h1:
        hero_h1.string = title

    # ── Hero meta spans (date / read-time) ────────────────────────────────────
    for span in soup.select(".blog-hero-meta span"):
        icon = span.find("i")
        if not icon:
            continue
        classes = " ".join(icon.get("class", []))
        if "calendar" in classes:
            span.clear()
            span.append(BeautifulSoup(
                f'<i class="far fa-calendar-alt"></i> {post_date}', "html.parser"))
        elif "clock" in classes:
            span.clear()
            span.append(BeautifulSoup(
                f'<i class="far fa-clock"></i> {read_time}', "html.parser"))

    # ── Article body ──────────────────────────────────────────────────────────
    article = soup.find("article", class_="blog-article")
    if article:
        # Preserve share-bar before clearing
        share_bar = article.find(class_="share-bar")
        if share_bar:
            share_bar = safe_copy(share_bar)

        article.clear()

        # Insert converted markdown HTML
        body_soup = BeautifulSoup(html_body, "html.parser")
        for child in list(body_soup.children):
            article.append(safe_copy(child))

        # Re-attach share bar with updated URLs
        if share_bar:
            for a in share_bar.find_all("a"):
                href = a.get("href", "")
                if "facebook" in href:
                    a["href"] = (
                        f"https://www.facebook.com/sharer/sharer.php?u={canon_url}"
                    )
                elif "twitter" in href or "x.com" in href:
                    enc = title.replace(" ", "+")
                    a["href"] = (
                        f"https://twitter.com/intent/tweet?url={canon_url}&text={enc}"
                    )
            article.append(share_bar)

    # ── Sidebar Table of Contents ─────────────────────────────────────────────
    toc_list = soup.find("ol", class_="toc-list")
    if toc_list and toc_entries:
        toc_list.clear()
        for entry in toc_entries:
            li   = soup.new_tag("li")
            link = soup.new_tag("a", href=f"#{entry['id']}")
            link.string = entry["text"]
            li.append(link)
            toc_list.append(li)


# =============================================================================
# FILE PROCESSOR
# =============================================================================

def process_file(md_path: Path, template_path: Path, lang: str) -> bool:
    """
    Read one .md file, inject into template, write .html next to it.
    Returns True on success, False on failure.
    """
    print(f"  {md_path.name}", end=" ... ", flush=True)

    raw_text = md_path.read_text(encoding="utf-8")

    # 1. Parse front-matter
    meta, body_md = parse_frontmatter(raw_text)

    # 2. Extract title (front-matter → H1 → filename)
    title = meta.get("title")
    if not title:
        title, body_md = extract_h1(body_md)
    if not title:
        title = md_path.stem.replace("-", " ").replace("_", " ").title()

    # 3. Derive slug
    slug = meta.get("slug") or slugify(md_path.stem)

    # 4. Convert markdown → HTML
    html_body = md_to_html(body_md)

    # 5. Build TOC from H2 headings
    toc_entries = build_toc(html_body)

    # 6. Load template (fresh parse each file)
    template_html = template_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(template_html, "html.parser")

    # 7. Inject everything
    inject(soup, meta, title, html_body, toc_entries, slug, lang)

    # 8. Write output
    out_path = md_path.with_suffix(".html")
    out_path.write_text(str(soup), encoding="utf-8")
    print(f"✅  → {out_path.name}")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    print("\n══════════════════════════════════════════════")
    print("   NY Special Ed — Guide Builder")
    print("══════════════════════════════════════════════\n")

    # Validate root folder
    if not GUIDES_DIR.exists():
        sys.exit(
            f"❌  Guides folder not found:\n    {GUIDES_DIR}\n\n"
            "    Edit the GUIDES_DIR variable at the top of build_guides.py"
        )

    # Validate English template
    if not EN_TEMPLATE.exists():
        sys.exit(f"❌  English template not found:\n    {EN_TEMPLATE}")

    # Check Spanish setup
    process_es = True
    if not ES_DIR.exists():
        print(f"  ℹ️   Spanish folder not found ({ES_DIR.name}/) — skipping.\n")
        process_es = False
    elif not ES_TEMPLATE.exists():
        print(f"  ⚠️   Spanish template not found ({ES_TEMPLATE.name}) — skipping.\n")
        process_es = False

    # ── English guides ─────────────────────────────────────────────────────────
    en_files = sorted(
        f for f in GUIDES_DIR.glob("*.md")
        if f.name.lower() not in ("readme.md", "index.md", "changelog.md")
    )

    if en_files:
        print(f"📄  English guides — {len(en_files)} file(s)\n"
              f"    Template: {EN_TEMPLATE.name}\n")
        ok = fail = 0
        for md_path in en_files:
            try:
                if process_file(md_path, EN_TEMPLATE, "en"):
                    ok += 1
                else:
                    fail += 1
            except Exception as exc:
                print(f"❌  {md_path.name} — {exc}")
                fail += 1
        print(f"\n    Result: {ok} succeeded, {fail} failed.\n")
    else:
        print("  ℹ️   No English .md files found in guides/\n")

    # ── Spanish guides ─────────────────────────────────────────────────────────
    if process_es:
        es_files = sorted(
            f for f in ES_DIR.glob("*.md")
            if f.name.lower() not in ("readme.md", "index.md", "changelog.md")
        )

        if es_files:
            print(f"📄  Spanish guides — {len(es_files)} file(s)\n"
                  f"    Template: {ES_TEMPLATE.name}\n")
            ok = fail = 0
            for md_path in es_files:
                try:
                    if process_file(md_path, ES_TEMPLATE, "es"):
                        ok += 1
                    else:
                        fail += 1
                except Exception as exc:
                    print(f"❌  {md_path.name} — {exc}")
                    fail += 1
            print(f"\n    Result: {ok} succeeded, {fail} failed.\n")
        else:
            print("  ℹ️   No Spanish .md files found in guides/es/\n")

    print("══════════════════════════════════════════════")
    print("  Build complete!")
    print("  Open any output .html file in your browser")
    print("  to preview before deploying.")
    print("══════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()