"""
Script 01 — Add "What Is an IEP?" hub card to ALL 34 NYC district index.html files
Run from site root: python3 scripts/01_add_hub_cards.py

- Reads the NYC district list from districts/index.html JS data
- Loops every districts/{slug}/index.html
- Appends a hub-card for what-is-an-iep.html if not already present
- Idempotent — safe to run multiple times
- Skips folders that don't exist yet (won't error)
"""

import json, re
from bs4 import BeautifulSoup
from pathlib import Path
import sys

DISTRICTS_INDEX = Path("districts/index.html")
BASE_URL = "https://www.newyorkspecialed.net"
IEP_FILENAME = "what-is-an-iep.html"
IEP_EMOJI = "📋"
IEP_TITLE = "What Is an IEP?"
IEP_DESC = "Plain-language guide to the IEP document, eligibility, and services in this district."

if not DISTRICTS_INDEX.exists():
    sys.exit(f"ERROR: {DISTRICTS_INDEX} not found — run from site root.")

# ── Pull district list from the JS const in districts/index.html ──────────────
raw = DISTRICTS_INDEX.read_text(encoding="utf-8")
match = re.search(r'const districts = (\[.*?\]);', raw, re.DOTALL)
if not match:
    sys.exit("ERROR: Could not find 'const districts' array in districts/index.html")

all_districts = json.loads(match.group(1))
nyc_districts = [d for d in all_districts if d["type"] == "nyc"]
print(f"Found {len(nyc_districts)} NYC districts in index.\n")

updated = 0
skipped_missing = 0
skipped_exists = 0

for district in sorted(nyc_districts, key=lambda d: d["slug"]):
    slug = district["slug"]
    index_path = Path(f"districts/{slug}/index.html")

    if not index_path.exists():
        print(f"  SKIP (folder not found):    {slug}")
        skipped_missing += 1
        continue

    soup = BeautifulSoup(index_path.read_text(encoding="utf-8"), "html.parser")
    hub_grid = soup.find("div", class_="hub-grid")

    if not hub_grid:
        print(f"  SKIP (no .hub-grid found):  {slug}")
        skipped_missing += 1
        continue

    iep_href = f"{BASE_URL}/districts/{slug}/{IEP_FILENAME}"
    existing_hrefs = {a.get("href", "") for a in hub_grid.find_all("a", class_="hub-card")}

    if iep_href in existing_hrefs:
        print(f"  SKIP (already present):     {slug}")
        skipped_exists += 1
        continue

    a_tag = soup.new_tag("a", href=iep_href)
    a_tag["class"] = "hub-card"

    h3 = soup.new_tag("h3", style="color: #0056b3; margin-top: 0;")
    h3.string = f"{IEP_EMOJI} {IEP_TITLE}"

    p = soup.new_tag("p")
    p.string = IEP_DESC

    a_tag.append(h3)
    a_tag.append(p)
    hub_grid.append(a_tag)

    index_path.write_text(str(soup), encoding="utf-8")
    updated += 1
    print(f"  ADDED →  {slug}")

print(f"""
── Summary ──────────────────────────────
  Cards added:          {updated}
  Already present:      {skipped_exists}
  Folder/grid missing:  {skipped_missing}
─────────────────────────────────────────
Done.
""")