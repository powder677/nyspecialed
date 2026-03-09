"""
Script 03 — Generate what-is-an-iep.html for all 34 NYC districts
Run from site root: python3 scripts/03_format_iep_pages.py
Run with --force   to regenerate pages that already exist

Strategy:
  Uses districts/nyc-district-01-lower-east-side/what-is-an-iep.html as the
  master template — it is already perfectly formatted. For every other district
  we do targeted replacements of all District 1 / Lower East Side strings,
  then write the result as districts/{slug}/what-is-an-iep.html

  This guarantees every output page is structurally identical to the live D01 page.
"""

import json, re, sys
from bs4 import BeautifulSoup
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
DISTRICTS_INDEX = Path("districts/index.html")
TEMPLATE_PATH   = Path("districts/nyc-district-01-lower-east-side/what-is-an-iep.html")
IEP_FILENAME    = "what-is-an-iep.html"
BASE_URL        = "https://www.newyorkspecialed.net"
D01_SLUG        = "nyc-district-01-lower-east-side"
FORCE           = "--force" in sys.argv

# ── District metadata: slug → (neighborhood, borough, district_num) ───────────
DISTRICT_META = {
    "nyc-district-01-lower-east-side":     ("Lower East Side / Chinatown",   "Manhattan",    "1"),
    "nyc-district-02-upper-east-side":     ("Upper East Side / Tribeca",     "Manhattan",    "2"),
    "nyc-district-03-upper-west-side":     ("Upper West Side",               "Manhattan",    "3"),
    "nyc-district-04-east-harlem":         ("East Harlem / El Barrio",       "Manhattan",    "4"),
    "nyc-district-05-central-harlem":      ("Central Harlem",                "Manhattan",    "5"),
    "nyc-district-06-washington-heights":  ("Washington Heights / Inwood",   "Manhattan",    "6"),
    "nyc-district-07-south-bronx":         ("South Bronx",                   "the Bronx",    "7"),
    "nyc-district-08-throgs-neck":         ("Throgs Neck / Pelham Bay",      "the Bronx",    "8"),
    "nyc-district-09-grand-concourse":     ("Grand Concourse / Highbridge",  "the Bronx",    "9"),
    "nyc-district-10-riverdale":           ("Riverdale / Kingsbridge",       "the Bronx",    "10"),
    "nyc-district-11-pelham-parkway":      ("Pelham Parkway / Morris Park",  "the Bronx",    "11"),
    "nyc-district-12-soundview":           ("Soundview / Hunts Point",       "the Bronx",    "12"),
    "nyc-district-13-brooklyn-heights":    ("Brooklyn Heights / Fort Greene","Brooklyn",     "13"),
    "nyc-district-14-williamsburg":        ("Williamsburg / Bushwick",       "Brooklyn",     "14"),
    "nyc-district-15-park-slope":          ("Park Slope / Sunset Park",      "Brooklyn",     "15"),
    "nyc-district-16-bed-stuy":            ("Bedford-Stuyvesant",            "Brooklyn",     "16"),
    "nyc-district-17-crown-heights":       ("Crown Heights",                 "Brooklyn",     "17"),
    "nyc-district-18-east-flatbush":       ("East Flatbush / Canarsie",      "Brooklyn",     "18"),
    "nyc-district-19-east-new-york":       ("East New York / Starrett City", "Brooklyn",     "19"),
    "nyc-district-20-bay-ridge":           ("Bay Ridge / Borough Park",      "Brooklyn",     "20"),
    "nyc-district-21-coney-island":        ("Coney Island / Gravesend",      "Brooklyn",     "21"),
    "nyc-district-22-midwood":             ("Midwood / Sheepshead Bay",      "Brooklyn",     "22"),
    "nyc-district-23-brownsville":         ("Brownsville",                   "Brooklyn",     "23"),
    "nyc-district-24-maspeth":             ("Maspeth / Middle Village",      "Queens",       "24"),
    "nyc-district-25-flushing":            ("Flushing / Whitestone",         "Queens",       "25"),
    "nyc-district-26-bayside":             ("Bayside / Little Neck",         "Queens",       "26"),
    "nyc-district-27-rockaway":            ("Rockaway / Howard Beach",       "Queens",       "27"),
    "nyc-district-28-forest-hills":        ("Forest Hills / Jamaica",        "Queens",       "28"),
    "nyc-district-29-queens-village":      ("Queens Village / Rosedale",     "Queens",       "29"),
    "nyc-district-30-astoria":             ("Astoria / Long Island City",    "Queens",       "30"),
    "nyc-district-31-staten-island":       ("Staten Island",                 "Staten Island","31"),
    "nyc-district-32-bushwick":            ("Bushwick",                      "Brooklyn",     "32"),
    "nyc-district-75":                     ("District 75 — Citywide",        "New York City","75"),
    "nyc-district-79":                     ("District 79 — Alternative",     "New York City","79"),
}

# D01 values that appear in the template — we'll replace these
D01_NEIGHBORHOOD = "Lower East Side / Chinatown"
D01_BOROUGH      = "Manhattan"
D01_NUM          = "1"

# ── Validate inputs ───────────────────────────────────────────────────────────
for p in [DISTRICTS_INDEX, TEMPLATE_PATH]:
    if not p.exists():
        sys.exit(f"ERROR: {p} not found — run from site root.")

template_text = TEMPLATE_PATH.read_text(encoding="utf-8")

raw = DISTRICTS_INDEX.read_text(encoding="utf-8")
match = re.search(r'const districts = (\[.*?\]);', raw, re.DOTALL)
if not match:
    sys.exit("ERROR: Could not find 'const districts' in districts/index.html")

all_districts  = json.loads(match.group(1))
nyc_districts  = [d for d in all_districts if d["type"] == "nyc"]
print(f"Found {len(nyc_districts)} NYC districts.")
print(f"Template: {TEMPLATE_PATH}")
if FORCE:
    print("  --force: regenerating all pages.\n")
else:
    print("  Skipping existing pages. Use --force to regenerate.\n")

# ── Process each district ─────────────────────────────────────────────────────
created = skipped_exists = skipped_missing = 0

for district in sorted(nyc_districts, key=lambda d: d["slug"]):
    slug = district["slug"]
    district_dir = Path(f"districts/{slug}")
    out_path     = district_dir / IEP_FILENAME

    # Skip D01 — it's already the template
    if slug == D01_SLUG:
        print(f"  SKIP (template district): {slug}")
        skipped_exists += 1
        continue

    if not district_dir.exists():
        print(f"  SKIP (folder not found):  {slug}")
        skipped_missing += 1
        continue

    if out_path.exists() and not FORCE:
        print(f"  SKIP (already exists):    {slug}")
        skipped_exists += 1
        continue

    neighborhood, borough, num = DISTRICT_META.get(
        slug, (f"District {slug}", "New York City", re.search(r'\d+', slug).group(0))
    )

    # ── String replacements on the full template text ─────────────────────────
    html = template_text

    # 1. All URL references to D01 slug  →  new slug
    html = html.replace(f"/districts/{D01_SLUG}/", f"/districts/{slug}/")
    html = html.replace(f"districts/{D01_SLUG}/", f"districts/{slug}/")

    # 2. Meta title
    html = html.replace(
        f"What Is an IEP? | NYC District {D01_NUM} – {D01_NEIGHBORHOOD} | NY Special Ed",
        f"What Is an IEP? | NYC District {num} – {neighborhood} | NY Special Ed"
    )

    # 3. Meta description
    html = html.replace(
        f"Plain-language guide to the IEP process, eligibility, and services for District {D01_NUM} families in {D01_NEIGHBORHOOD}, {D01_BOROUGH}.",
        f"Plain-language guide to the IEP process, eligibility, and services for District {num} families in {neighborhood}, {borough}."
    )

    # 4. Back link text
    html = html.replace(
        f"← Back to District {D01_NUM} Hub",
        f"← Back to District {num} Hub"
    )

    # 5. Eyebrow
    html = html.replace(
        f"District {D01_NUM} · IEP Guide",
        f"District {num} · IEP Guide"
    )

    # 6. H1
    html = html.replace(
        f"What Is an IEP in NYC District {D01_NUM}?",
        f"What Is an IEP in NYC District {num}?"
    )

    # 7. Intro paragraph
    html = html.replace(
        f"what it is, how it works in {D01_NEIGHBORHOOD}, and what rights you have as a parent.",
        f"what it is, how it works in {neighborhood}, and what rights you have as a parent."
    )

    # 8. Opening body paragraph (neighborhood + borough mentions)
    html = html.replace(
        f"In NYC District {D01_NUM} — serving {D01_NEIGHBORHOOD} —",
        f"In NYC District {num} — serving {neighborhood} —"
    )
    html = html.replace(
        f"As a parent or guardian in {D01_BOROUGH},",
        f"As a parent or guardian in {borough},"
    )

    # 9. Next Steps internal links (district number in text)
    html = html.replace(
        f"Evaluation Process</a> page for District {D01_NUM}.",
        f"Evaluation Process</a> page for District {num}."
    )
    html = html.replace(
        f"CSE Meeting Guide</a> for District {D01_NUM}.",
        f"CSE Meeting Guide</a> for District {num}."
    )

    # 10. CTA box
    html = html.replace(
        f"toolkit for District {D01_NUM} parents.",
        f"toolkit for District {num} parents."
    )

    # ── Write output ──────────────────────────────────────────────────────────
    out_path.write_text(html, encoding="utf-8")
    created += 1
    print(f"  CREATED →  districts/{slug}/{IEP_FILENAME}")

print(f"""
── Summary ──────────────────────────────
  Pages created:        {created}
  Skipped (exists):     {skipped_exists}
  Skipped (missing):    {skipped_missing}
─────────────────────────────────────────
Done.{"  Re-run with --force to overwrite existing pages." if skipped_exists > 1 else ""}
""")