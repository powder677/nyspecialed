"""
Script 02 — Add "📋 What Is an IEP?" to the district-subnav on every page
            in every NYC district folder.
Run from site root: python3 scripts/02_update_subnavs.py

- Reads the NYC district list from districts/index.html JS data  
- For each district folder, scans ALL .html files
- Appends the IEP link to every district-subnav found
- Marks subnav-active ONLY on what-is-an-iep.html itself
- Idempotent — safe to run multiple times
- Skips folders that don't exist yet
"""

import json, re
from bs4 import BeautifulSoup
from pathlib import Path
import sys

DISTRICTS_INDEX = Path("districts/index.html")
BASE_URL = "https://www.newyorkspecialed.net"
IEP_FILENAME = "what-is-an-iep.html"
IEP_LABEL = "📋 What Is an IEP?"

if not DISTRICTS_INDEX.exists():
    sys.exit(f"ERROR: {DISTRICTS_INDEX} not found — run from site root.")

# ── Pull district list ────────────────────────────────────────────────────────
raw = DISTRICTS_INDEX.read_text(encoding="utf-8")
match = re.search(r'const districts = (\[.*?\]);', raw, re.DOTALL)
if not match:
    sys.exit("ERROR: Could not find 'const districts' array in districts/index.html")

all_districts = json.loads(match.group(1))
nyc_districts = [d for d in all_districts if d["type"] == "nyc"]
print(f"Found {len(nyc_districts)} NYC districts. Processing all subnavs...\n")

total_updated = 0
total_skipped_missing = 0
total_skipped_exists = 0

for district in sorted(nyc_districts, key=lambda d: d["slug"]):
    slug = district["slug"]
    district_dir = Path(f"districts/{slug}")

    if not district_dir.exists():
        print(f"  SKIP (folder not found): {slug}")
        total_skipped_missing += 1
        continue

    pages = sorted(district_dir.glob("*.html"))
    if not pages:
        print(f"  SKIP (no html files):    {slug}")
        total_skipped_missing += 1
        continue

    iep_href = f"{BASE_URL}/districts/{slug}/{IEP_FILENAME}"
    district_updated = 0

    for filepath in pages:
        soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "html.parser")
        subnavs = soup.find_all("nav", class_="district-subnav")

        if not subnavs:
            continue  # page has no subnav — not an error

        changed = False
        for subnav in subnavs:
            existing_hrefs = [a.get("href", "") for a in subnav.find_all("a")]
            if iep_href in existing_hrefs:
                continue  # already present in this nav block

            new_a = soup.new_tag("a", href=iep_href)
            new_a.string = IEP_LABEL

            # Only mark active on the IEP page itself
            if filepath.name == IEP_FILENAME:
                new_a["class"] = "subnav-active"
                new_a["aria-current"] = "page"

            subnav.append(new_a)
            changed = True

        if changed:
            filepath.write_text(str(soup), encoding="utf-8")
            district_updated += 1
            total_updated += 1

    if district_updated:
        print(f"  UPDATED {district_updated} page(s) in: {slug}")
    else:
        total_skipped_exists += 1
        print(f"  SKIP (all up to date):   {slug}")

print(f"""
── Summary ──────────────────────────────
  Pages updated:        {total_updated}
  Districts up to date: {total_skipped_exists}
  Folders missing:      {total_skipped_missing}
─────────────────────────────────────────
Done.
""")