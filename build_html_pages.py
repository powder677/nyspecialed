#!/usr/bin/env python3
"""
IEP Page Builder
================
Converts generated .md files into HTML pages, routed by language.

Expected input structure (output from generate_iep_pages.py):
  output/
    nyc-district-06-washington-heights.md       ← English
    es/
      nyc-district-06-washington-heights.md     ← Spanish

Output structure:
  districts/
    nyc-district-06-washington-heights/
      what-is-an-iep.html                       ← English
  es/distritos/
    nyc-district-06-washington-heights/
      que-es-un-iep.html                        ← Spanish

Usage:
  pip install python-frontmatter markdown beautifulsoup4
  python build_html_pages.py
"""

import os
import frontmatter
import markdown
from bs4 import BeautifulSoup
from pathlib import Path

# ──────────────────────────────────────────────
# CONFIG  ← match these to your site structure
# ──────────────────────────────────────────────
CONTENT_DIR      = "output"          # where generate_iep_pages.py wrote .md files
EN_DISTRICTS_DIR = "districts"       # English output: districts/{slug}/{filename}.html
ES_DISTRICTS_DIR = "es/distritos"    # Spanish output: es/distritos/{slug}/{filename}.html
BASE_URL         = "https://newyorkspecialed.net"

# ──────────────────────────────────────────────
# SHORT AREA NAMES  ← used in the HTML filename for SEO
# e.g.  what-is-an-iep-south-bronx.html
#        que-es-un-iep-washington-heights.html
# ──────────────────────────────────────────────
SLUG_TO_AREA = {
    "nyc-district-01-lower-east-side-chinatown":   "lower-east-side",
    "nyc-district-02-tribeca-greenwich-village":    "tribeca",
    "nyc-district-03-upper-west-side":              "upper-west-side",
    "nyc-district-04-east-harlem":                  "east-harlem",
    "nyc-district-05-central-harlem":               "central-harlem",
    "nyc-district-06-washington-heights":           "washington-heights",
    "nyc-district-07-south-bronx":                  "south-bronx",
    "nyc-district-08-hunts-point-morrisania":       "hunts-point",
    "nyc-district-09-tremont-belmont":              "tremont",
    "nyc-district-10-fordham-riverdale":            "riverdale",
    "nyc-district-11-pelham-parkway-morris-park":   "pelham-parkway",
    "nyc-district-12-wakefield-williamsbridge":     "williamsbridge",
    "nyc-district-13-brooklyn-heights-fort-greene": "brooklyn-heights",
    "nyc-district-14-williamsburg-greenpoint":      "williamsburg",
    "nyc-district-15-park-slope-red-hook":          "park-slope",
    "nyc-district-16-bushwick-bedford-stuyvesant":  "bedford-stuyvesant",
    "nyc-district-17-crown-heights-flatbush":       "crown-heights",
    "nyc-district-18-canarsie-flatlands":           "canarsie",
    "nyc-district-19-east-new-york-starrett-city":  "east-new-york",
    "nyc-district-20-bay-ridge-bensonhurst":        "bay-ridge",
    "nyc-district-21-coney-island-brighton-beach":  "coney-island",
    "nyc-district-22-flatbush-marine-park":         "flatbush",
    "nyc-district-23-brownsville":                  "brownsville",
    "nyc-district-24-middle-village-ridgewood":     "ridgewood",
    "nyc-district-25-flushing-whitestone":          "flushing",
    "nyc-district-26-bayside-little-neck":          "bayside",
    "nyc-district-27-jamaica-howard-beach":         "jamaica",
    "nyc-district-28-forest-hills-richmond-hill":   "forest-hills",
    "nyc-district-29-springfield-gardens-hollis":   "springfield-gardens",
    "nyc-district-30-astoria-long-island-city":     "astoria",
    "nyc-district-31-staten-island":                "staten-island",
    "nyc-district-32-bushwick":                     "bushwick",
}


def get_css_path(language: str) -> str:
    """
    Return correct relative path to CSS based on folder depth.
      English: districts/slug/file.html  → ../../styles/
      Spanish: es/distritos/slug/file.html → ../../../styles/
    """
    if language == "es":
        return "../../../styles"
    return "../../styles"


def build_html_page(
    target_file: str,
    title: str,
    meta_desc: str,
    body_html: str,
    lang: str,
    slug: str,
    en_filename: str,
    es_filename: str,
) -> None:
    css_path = get_css_path(lang)

    en_url = f"{BASE_URL}/districts/{slug}/{en_filename}"
    es_url = f"{BASE_URL}/districts/{slug}/{es_filename}"

    hreflang_tags = f"""
    <link rel="alternate" hreflang="en" href="{en_url}">
    <link rel="alternate" hreflang="es" href="{es_url}">
    <link rel="alternate" hreflang="x-default" href="{en_url}">"""

    html_shell = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta_desc}">
    <link rel="stylesheet" href="{css_path}/global.css">
    <link rel="stylesheet" href="{css_path}/styles-nav-footer.css">
    {hreflang_tags}
</head>
<body>
    <main class="container page-content">
        <article>
            {body_html}
        </article>
    </main>
</body>
</html>"""

    soup = BeautifulSoup(html_shell, "html.parser")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())


def clean_frontmatter(raw: str) -> str:
    """
    Claude sometimes wraps YAML in a code fence like:
        ```yaml
        ---
        slug: ...
        ---
        ```
    Strip any leading ```yaml / ``` wrappers so python-frontmatter can parse it.
    """
    lines = raw.splitlines()

    # Remove leading ```yaml or ``` line
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]

    # Remove trailing ``` line
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines)


def slug_from_filename(filepath: str) -> str:
    """Derive slug from the filename itself as a fallback."""
    return Path(filepath).stem   # e.g. "nyc-district-06-washington-heights"


def lang_from_path(filepath: str) -> str:
    """Detect language from folder path: output/es/... → es, else en."""
    parts = Path(filepath).parts
    return "es" if "es" in parts else "en"


def process_file(filepath: str) -> None:
    """Process a single .md file into an HTML page."""
    raw = Path(filepath).read_text(encoding="utf-8")
    raw = clean_frontmatter(raw)

    post = frontmatter.loads(raw)

    # Pull metadata — fall back to filename/path when frontmatter is missing
    district_slug = post.get("slug") or slug_from_filename(filepath)
    language      = post.get("language") or lang_from_path(filepath)
    page_type     = post.get("page_type") or ("que-es-un-iep" if language == "es" else "what-is-an-iep")
    seo_title     = post.get("seo_title", "")
    meta_desc     = post.get("meta_description", "")

    if not district_slug:
        print(f"  ⚠️  Skipped (no slug): {filepath}")
        return

    # Convert markdown body → HTML
    html_content = markdown.markdown(
        post.content,
        extensions=["tables", "fenced_code"]
    )

    # Build SEO filenames using short area name
    area = SLUG_TO_AREA.get(district_slug, district_slug)
    en_filename = f"what-is-an-iep-{area}"
    es_filename = f"que-es-un-iep-{area}"
    filename    = es_filename if language == "es" else en_filename

    # Route to correct output directory
    base_dir = ES_DISTRICTS_DIR if language == "es" else EN_DISTRICTS_DIR
    target_dir = os.path.join(base_dir, district_slug)
    os.makedirs(target_dir, exist_ok=True)

    target_file = os.path.join(target_dir, f"{filename}.html")
    build_html_page(target_file, seo_title, meta_desc, html_content, language, district_slug, en_filename, es_filename)
    print(f"  ✅ [{language.upper()}] {target_file}")


def process_all() -> None:
    content_path = Path(CONTENT_DIR)

    if not content_path.exists():
        print(f"❌  Input directory '{CONTENT_DIR}' not found.")
        print(f"    Run generate_iep_pages.py first to create .md files.")
        return

    # Walk recursively so es/ subfolder is included
    md_files = list(content_path.rglob("*.md"))

    if not md_files:
        print(f"❌  No .md files found in '{CONTENT_DIR}/'")
        return

    print(f"\n🔨  Building HTML pages from {len(md_files)} .md files...\n")

    success = 0
    for filepath in sorted(md_files):
        try:
            process_file(str(filepath))
            success += 1
        except Exception as exc:
            print(f"  ❌  Error processing {filepath}: {exc}")

    print(f"\n{'─'*50}")
    print(f"  Done: {success}/{len(md_files)} pages built")
    print(f"  English → {EN_DISTRICTS_DIR}/")
    print(f"  Spanish → {ES_DISTRICTS_DIR}/\n")


if __name__ == "__main__":
    process_all()