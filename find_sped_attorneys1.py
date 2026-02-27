"""
find_sped_attorneys.py
-----------------------
Finds special education attorneys who have appeared in impartial hearings
for each of your 52 NY districts, then enriches results with contact info
using Vertex AI (Gemini with Google Search grounding).

DATA SOURCES:
  1. NYSED SRO (State Review Office) — public PDF decisions at sro.nysed.gov
     These name the attorneys who argued the case. We extract "parent's attorney"
     from the appearance section of each decision.
  2. Vertex AI + Google Search grounding — find firm website, phone, email for
     each extracted attorney name.

OUTPUT:
  attorneys.json   — full structured results, all districts
  attorneys.csv    — flat table for Excel review
  attorneys_review.html — quick visual review page

After review you manually paste the best leads into your outreach list.
The script does NOT auto-inject into site pages — you review first.

SETUP:
  pip install google-cloud-aiplatform requests beautifulsoup4 pdfplumber lxml --break-system-packages
  gcloud auth application-default login

USAGE:
  python find_sped_attorneys.py                           # all districts
  python find_sped_attorneys.py --district albany-city-sd # one district
  python find_sped_attorneys.py --skip-sro                # Vertex only (no PDF scrape)
  python find_sped_attorneys.py --dry-run                 # show what would run
"""

import argparse
import csv
import json
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from vertexai.generative_models import grounding

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
GCP_PROJECT_ID   = "ny-build-487810"
GCP_REGION       = "us-central1"
GEMINI_MODEL     = "gemini-2.0-flash"

OUTPUT_DIR       = Path(r"C:\Users\elisa\OneDrive\Documents\github\nyspecialedsite\attorney-research")
RATE_LIMIT_DELAY = 4   # seconds between Vertex calls
SRO_DELAY        = 2   # seconds between SRO requests

SRO_BASE         = "https://www.sro.nysed.gov"
SRO_DECISIONS_URL = "https://www.sro.nysed.gov/decisions"

# ──────────────────────────────────────────────
#  DISTRICT MAP
#  slug → search terms used to match SRO decisions
#  and to guide Vertex search
# ──────────────────────────────────────────────
DISTRICTS = {
    "albany-city-sd":          {"name": "Albany City SD",         "city": "Albany",       "county": "Albany",     "sro_terms": ["Albany City", "Albany School District"]},
    "buffalo-city-sd":         {"name": "Buffalo City SD",        "city": "Buffalo",      "county": "Erie",       "sro_terms": ["Buffalo City", "Buffalo School"]},
    "rochester-city-sd":       {"name": "Rochester City SD",      "city": "Rochester",    "county": "Monroe",     "sro_terms": ["Rochester City", "Rochester School"]},
    "syracuse-city-sd":        {"name": "Syracuse City SD",       "city": "Syracuse",     "county": "Onondaga",   "sro_terms": ["Syracuse City", "Syracuse School"]},
    "yonkers-city-sd":         {"name": "Yonkers City SD",        "city": "Yonkers",      "county": "Westchester","sro_terms": ["Yonkers City", "Yonkers School"]},
    "nyc-district-01-lower-east-side":  {"name": "NYC District 1",  "city": "Manhattan", "county": "New York",   "sro_terms": ["New York City School District", "NYC District 1", "Community School District 1"]},
    "nyc-district-02-upper-east-side":  {"name": "NYC District 2",  "city": "Manhattan", "county": "New York",   "sro_terms": ["NYC District 2", "Community School District 2", "New York City"]},
    "nyc-district-03-upper-west-side":  {"name": "NYC District 3",  "city": "Manhattan", "county": "New York",   "sro_terms": ["NYC District 3", "Community School District 3", "New York City"]},
    "nyc-district-04-east-harlem":      {"name": "NYC District 4",  "city": "Manhattan", "county": "New York",   "sro_terms": ["NYC District 4", "New York City"]},
    "nyc-district-05-central-harlem":   {"name": "NYC District 5",  "city": "Manhattan", "county": "New York",   "sro_terms": ["NYC District 5", "New York City"]},
    "nyc-district-06-washington-heights":{"name": "NYC District 6", "city": "Manhattan", "county": "New York",   "sro_terms": ["NYC District 6", "New York City"]},
    "nyc-district-13-brooklyn-heights": {"name": "NYC District 13", "city": "Brooklyn",  "county": "Kings",      "sro_terms": ["NYC District 13", "New York City"]},
    "nyc-district-15-park-slope":       {"name": "NYC District 15", "city": "Brooklyn",  "county": "Kings",      "sro_terms": ["NYC District 15", "New York City"]},
    "nyc-district-20-bay-ridge":        {"name": "NYC District 20", "city": "Brooklyn",  "county": "Kings",      "sro_terms": ["NYC District 20", "New York City"]},
    "nyc-district-22-flatbush":         {"name": "NYC District 22", "city": "Brooklyn",  "county": "Kings",      "sro_terms": ["NYC District 22", "New York City"]},
    "nyc-district-24-corona":           {"name": "NYC District 24", "city": "Queens",    "county": "Queens",     "sro_terms": ["NYC District 24", "New York City"]},
    "nyc-district-26-bayside":          {"name": "NYC District 26", "city": "Queens",    "county": "Queens",     "sro_terms": ["NYC District 26", "New York City"]},
    "nyc-district-28-forest-hills":     {"name": "NYC District 28", "city": "Queens",    "county": "Queens",     "sro_terms": ["NYC District 28", "New York City"]},
    "nyc-district-30-astoria":          {"name": "NYC District 30", "city": "Queens",    "county": "Queens",     "sro_terms": ["NYC District 30", "New York City"]},
    "nyc-district-31-staten-island":    {"name": "NYC District 31", "city": "Staten Island","county": "Richmond","sro_terms": ["NYC District 31", "New York City"]},
    "nyc-district-75":                  {"name": "NYC District 75", "city": "New York City","county": "Citywide", "sro_terms": ["District 75", "NYC District 75", "New York City"]},
}

# Fill remaining districts up to 52 — add yours here
# Pattern: "slug": {"name": "...", "city": "...", "county": "...", "sro_terms": ["..."]}
ADDITIONAL_DISTRICTS = {
    "great-neck-ufsd":         {"name": "Great Neck UFSD",       "city": "Great Neck",   "county": "Nassau",     "sro_terms": ["Great Neck"]},
    "herricks-ufsd":           {"name": "Herricks UFSD",         "city": "New Hyde Park","county": "Nassau",     "sro_terms": ["Herricks"]},
    "lawrence-ufsd":           {"name": "Lawrence UFSD",         "city": "Lawrence",     "county": "Nassau",     "sro_terms": ["Lawrence Union Free"]},
    "levittown-ufsd":          {"name": "Levittown UFSD",        "city": "Levittown",    "county": "Nassau",     "sro_terms": ["Levittown"]},
    "north-shore-csd":         {"name": "North Shore CSD",       "city": "Glen Head",    "county": "Nassau",     "sro_terms": ["North Shore Central"]},
    "sewanhaka-csd":           {"name": "Sewanhaka CSD",         "city": "Floral Park",  "county": "Nassau",     "sro_terms": ["Sewanhaka"]},
    "valley-stream-ufsd":      {"name": "Valley Stream UFSD",    "city": "Valley Stream","county": "Nassau",     "sro_terms": ["Valley Stream"]},
    "brentwood-ufsd":          {"name": "Brentwood UFSD",        "city": "Brentwood",    "county": "Suffolk",    "sro_terms": ["Brentwood"]},
    "central-islip-ufsd":      {"name": "Central Islip UFSD",    "city": "Central Islip","county": "Suffolk",    "sro_terms": ["Central Islip"]},
    "longwood-csd":            {"name": "Longwood CSD",          "city": "Middle Island","county": "Suffolk",    "sro_terms": ["Longwood Central"]},
    "south-huntington-ufsd":   {"name": "South Huntington UFSD", "city": "Huntington Station","county": "Suffolk","sro_terms": ["South Huntington"]},
    "three-village-csd":       {"name": "Three Village CSD",     "city": "East Setauket","county": "Suffolk",    "sro_terms": ["Three Village"]},
    "william-floyd-ufsd":      {"name": "William Floyd UFSD",    "city": "Mastic Beach", "county": "Suffolk",    "sro_terms": ["William Floyd"]},
    "ardsley-ufsd":            {"name": "Ardsley UFSD",          "city": "Ardsley",      "county": "Westchester","sro_terms": ["Ardsley"]},
    "mount-vernon-city-sd":    {"name": "Mount Vernon City SD",  "city": "Mount Vernon", "county": "Westchester","sro_terms": ["Mount Vernon"]},
    "new-rochelle-city-sd":    {"name": "New Rochelle City SD",  "city": "New Rochelle", "county": "Westchester","sro_terms": ["New Rochelle"]},
    "scarsdale-ufsd":          {"name": "Scarsdale UFSD",        "city": "Scarsdale",    "county": "Westchester","sro_terms": ["Scarsdale"]},
    "white-plains-city-sd":    {"name": "White Plains City SD",  "city": "White Plains", "county": "Westchester","sro_terms": ["White Plains"]},
    "newburgh-city-sd":        {"name": "Newburgh City SD",      "city": "Newburgh",     "county": "Orange",     "sro_terms": ["Newburgh"]},
    "poughkeepsie-city-sd":    {"name": "Poughkeepsie City SD",  "city": "Poughkeepsie", "county": "Dutchess",   "sro_terms": ["Poughkeepsie City"]},
    "troy-city-sd":            {"name": "Troy City SD",          "city": "Troy",         "county": "Rensselaer", "sro_terms": ["Troy City", "Troy School"]},
    "schenectady-city-sd":     {"name": "Schenectady City SD",   "city": "Schenectady",  "county": "Schenectady","sro_terms": ["Schenectady City"]},
    "utica-city-sd":           {"name": "Utica City SD",         "city": "Utica",        "county": "Oneida",     "sro_terms": ["Utica City", "Utica School"]},
    "rome-city-sd":            {"name": "Rome City SD",          "city": "Rome",         "county": "Oneida",     "sro_terms": ["Rome City School", "Rome Central"]},
    "binghamton-city-sd":      {"name": "Binghamton City SD",    "city": "Binghamton",   "county": "Broome",     "sro_terms": ["Binghamton City", "Binghamton School"]},
    "elmira-city-sd":          {"name": "Elmira City SD",        "city": "Elmira",       "county": "Chemung",    "sro_terms": ["Elmira City", "Elmira School"]},
    "ithaca-city-sd":          {"name": "Ithaca City SD",        "city": "Ithaca",       "county": "Tompkins",   "sro_terms": ["Ithaca City", "Ithaca School"]},
    "kingston-city-sd":        {"name": "Kingston City SD",      "city": "Kingston",     "county": "Ulster",     "sro_terms": ["Kingston City", "Kingston School"]},
    "middletown-city-sd":      {"name": "Middletown City SD",    "city": "Middletown",   "county": "Orange",     "sro_terms": ["Middletown City", "Middletown School"]},
    "port-chester-rye-ufsd":   {"name": "Port Chester-Rye UFSD","city": "Port Chester",  "county": "Westchester","sro_terms": ["Port Chester"]},
    "hempstead-ufsd":          {"name": "Hempstead UFSD",        "city": "Hempstead",    "county": "Nassau",     "sro_terms": ["Hempstead Union Free"]},
}
DISTRICTS.update(ADDITIONAL_DISTRICTS)


# ══════════════════════════════════════════════
#  SRO SCRAPING
# ══════════════════════════════════════════════

def fetch_sro_decision_index(year: int = 2024) -> list[dict]:
    """
    Fetch the SRO decisions index for a given year.
    Returns list of {number, title, url} dicts.
    """
    url = f"{SRO_BASE}/decisions/{year}"
    headers = {"User-Agent": "Mozilla/5.0 (research bot)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        log.warning(f"  SRO index fetch failed ({year}): {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    decisions = []

    # SRO page has a table or list of decisions with links to PDFs/HTML
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)
        if not text:
            continue
        # SRO decision links typically contain the decision number
        if re.search(r"\d{2}-\d{3}|\d{5}", text) or "decision" in href.lower():
            full_url = href if href.startswith("http") else SRO_BASE + href
            decisions.append({"title": text, "url": full_url})

    return decisions


def extract_attorney_from_sro_html(url: str, district_terms: list[str]) -> dict | None:
    """
    Fetch a single SRO decision page and extract:
    - district name mentioned
    - parent's attorney name
    - any law firm name
    Returns None if district not mentioned or no attorney found.
    """
    headers = {"User-Agent": "Mozilla/5.0 (research bot)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        text = resp.text
    except Exception as e:
        log.debug(f"  SRO decision fetch failed: {e}")
        return None

    # Check if this decision involves our district
    district_match = False
    for term in district_terms:
        if term.lower() in text.lower():
            district_match = True
            break
    if not district_match:
        return None

    soup = BeautifulSoup(text, "lxml")
    full_text = soup.get_text(separator=" ", strip=True)

    # Look for appearance/representation patterns
    # SRO decisions typically have "Appearances:" section
    # "For the Petitioner: [Attorney Name], Esq., [Firm]"
    # "For the Parent: [Attorney Name], Esq."
    patterns = [
        # "For the Petitioner: John Smith, Esq."
        r"For the [Pp]etitioner[:\s]+([A-Z][a-zA-Z\s,\.]+?),?\s*Esq",
        r"For the [Pp]arent[:\s]+([A-Z][a-zA-Z\s,\.]+?),?\s*Esq",
        r"[Pp]etitioner(?:'s)?\s+[Aa]ttorney[:\s]+([A-Z][a-zA-Z\s,\.]+?),?\s*Esq",
        r"[Pp]arent(?:'s)?\s+[Cc]ounsel[:\s]+([A-Z][a-zA-Z\s,\.]+?),?\s*Esq",
        r"([A-Z][a-zA-Z\s\.]+),\s*Esq\..*?(?:for|on behalf of)\s+(?:the\s+)?[Pp]etitioner",
        # Firm name patterns
        r"For the [Pp]etitioner[:\s]+([A-Z][a-zA-Z\s&,\.]+(?:Law|Legal|LLP|LLC|PC|P\.C\.|P\.A\.))",
        r"For the [Pp]arent[:\s]+([A-Z][a-zA-Z\s&,\.]+(?:Law|Legal|LLP|LLC|PC|P\.C\.|P\.A\.))",
    ]

    attorneys = []
    for pattern in patterns:
        matches = re.findall(pattern, full_text)
        for m in matches:
            name = m.strip().strip(",").strip()
            if len(name) > 3 and len(name) < 80:
                attorneys.append(name)

    if not attorneys:
        return None

    # Get the decision number/title from URL or page
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    return {
        "source_url":  url,
        "decision":    title[:100],
        "attorneys":   list(dict.fromkeys(attorneys)),  # dedupe, preserve order
    }


# ══════════════════════════════════════════════
#  VERTEX AI ENRICHMENT
# ══════════════════════════════════════════════

def build_enrichment_prompt(district_name: str, city: str, county: str,
                             known_names: list[str]) -> str:
    known_section = ""
    if known_names:
        names_list = "\n".join(f"  - {n}" for n in known_names[:10])
        known_section = f"""
ATTORNEYS ALREADY IDENTIFIED FROM SRO DECISIONS:
{names_list}
For each of these, find their firm name, website URL, phone number, and email if available.
Also find any additional attorneys not on this list.
"""

    return f"""You are a legal research assistant helping identify special education 
attorneys who practice in {district_name} ({city}, {county} County, New York).

Search for:
1. Attorneys who have appeared in NYSED impartial hearings or SRO appeals 
   representing PARENTS (not school districts) in {district_name} or {county} County
2. Law firms specializing in special education, disability rights, or education law
   serving {city} and {county} County NY
3. Attorneys affiliated with organizations like Advocates for Children, DRNY,
   Legal Aid that serve this area
{known_section}
For each attorney or firm found, return ONLY raw JSON. No markdown. No explanation.

{{
  "district": "{district_name}",
  "attorneys": [
    {{
      "name": "Full Name",
      "title": "Esq. / Attorney / Advocate",
      "firm": "Firm or Organization Name",
      "website": "https://...",
      "phone": "XXX-XXX-XXXX",
      "email": "...",
      "focus": "brief description of specialty",
      "serves": "{county} County / {city}",
      "source": "where found (SRO decision / bar listing / firm website)",
      "confidence": "high / medium / low"
    }}
  ],
  "notes": "any relevant context about special ed legal landscape in this area"
}}

RULES:
- Only include attorneys who represent PARENTS, not school districts
- Minimum 1, maximum 6 attorneys per district
- Only include if you can find at least a name AND firm or website
- confidence=high means you found actual contact info
- confidence=medium means you found name and firm but not direct contact
- confidence=low means you found a name reference but limited details
- Do not invent contact information
- Set phone/email to null if not found
"""


def enrich_with_vertex(model, district_name: str, city: str, county: str,
                        known_names: list[str]) -> dict | None:
    """Use Vertex AI with Google Search grounding to find attorney contact info."""
    prompt = build_enrichment_prompt(district_name, city, county, known_names)

    try:
        # Use Google Search grounding for real-time web lookup
        google_search_tool = Tool.from_google_search_retrieval(
            grounding.GoogleSearchRetrieval(
                dynamic_retrieval_config=grounding.DynamicRetrievalConfig(
                    dynamic_threshold=0.3
                )
            )
        )
        response = model.generate_content(
            prompt,
            tools=[google_search_tool],
        )
        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"  JSON parse error for {district_name}: {e}")
        log.debug(f"  Raw: {response.text[:300]}")
        return None
    except Exception as e:
        log.error(f"  Vertex error for {district_name}: {e}")
        return None


# ══════════════════════════════════════════════
#  OUTPUT WRITERS
# ══════════════════════════════════════════════

def write_outputs(all_results: dict):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── JSON ──────────────────────────────────────────────────────
    json_path = OUTPUT_DIR / "attorneys.json"
    json_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    log.info(f"  ✓ attorneys.json")

    # ── CSV ───────────────────────────────────────────────────────
    csv_path = OUTPUT_DIR / "attorneys.csv"
    rows = []
    for slug, data in all_results.items():
        district_name = data.get("district", slug)
        for atty in data.get("attorneys", []):
            rows.append({
                "slug":       slug,
                "district":   district_name,
                "name":       atty.get("name", ""),
                "firm":       atty.get("firm", ""),
                "website":    atty.get("website", ""),
                "phone":      atty.get("phone", ""),
                "email":      atty.get("email", ""),
                "focus":      atty.get("focus", ""),
                "confidence": atty.get("confidence", ""),
                "source":     atty.get("source", ""),
            })
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log.info(f"  ✓ attorneys.csv ({len(rows)} rows)")

    # ── HTML review page ──────────────────────────────────────────
    html_path = OUTPUT_DIR / "attorneys_review.html"
    cards = ""
    for slug, data in all_results.items():
        district_name = data.get("district", slug)
        attorneys = data.get("attorneys", [])
        if not attorneys:
            continue
        atty_cards = ""
        for atty in attorneys:
            conf_color = {"high": "#16a34a", "medium": "#d97706", "low": "#9ca3af"}.get(
                atty.get("confidence", "low"), "#9ca3af"
            )
            phone_html = f'<a href="tel:{atty["phone"]}">{atty["phone"]}</a>' if atty.get("phone") else "—"
            email_html = f'<a href="mailto:{atty["email"]}">{atty["email"]}</a>' if atty.get("email") else "—"
            web_html   = f'<a href="{atty["website"]}" target="_blank">{atty["website"][:40]}…</a>' if atty.get("website") else "—"
            atty_cards += f"""
            <div style="border:1px solid #e2e8f0;border-radius:6px;padding:12px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <strong>{atty.get("name","")}</strong>
                <span style="font-size:0.75rem;color:{conf_color};font-weight:600;text-transform:uppercase;">{atty.get("confidence","")}</span>
              </div>
              <div style="color:#6b7280;font-size:0.85rem;margin:4px 0;">{atty.get("firm","")}</div>
              <div style="font-size:0.8rem;margin-top:6px;">
                📞 {phone_html} &nbsp; ✉ {email_html} &nbsp; 🌐 {web_html}
              </div>
              <div style="font-size:0.75rem;color:#9ca3af;margin-top:4px;">{atty.get("focus","")} — {atty.get("source","")}</div>
            </div>"""
        cards += f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-size:1rem;font-weight:700;color:#1e3a8a;border-bottom:2px solid #e2e8f0;padding-bottom:6px;">{district_name} <span style="font-weight:400;color:#9ca3af;font-size:0.85rem;">({slug})</span></h2>
          {atty_cards}
          {f'<p style="font-size:0.8rem;color:#6b7280;font-style:italic;">{data.get("notes","")}</p>' if data.get("notes") else ""}
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>NY Special Ed Attorney Research</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1f2937; }}
  h1 {{ color: #1e3a8a; }}
  a {{ color: #0056b3; }}
</style>
</head>
<body>
<h1>NY Special Ed Attorney Research</h1>
<p style="color:#6b7280;">Generated by find_sped_attorneys.py — review before using. Verify all contact info independently.</p>
<hr/>
{cards}
</body>
</html>"""
    html_path.write_text(html, encoding="utf-8")
    log.info(f"  ✓ attorneys_review.html")


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--district",  type=str, default=None, help="Single district slug")
    parser.add_argument("--skip-sro",  action="store_true",    help="Skip SRO scraping, Vertex only")
    parser.add_argument("--dry-run",   action="store_true",    help="Show plan, no API calls")
    parser.add_argument("--year",      type=int, default=2024, help="SRO decisions year to search (default 2024)")
    args = parser.parse_args()

    # Filter districts
    districts = {
        slug: info for slug, info in DISTRICTS.items()
        if args.district is None or slug == args.district
    }
    log.info(f"Districts to process: {len(districts)}")

    if args.dry_run:
        for slug, info in districts.items():
            log.info(f"  Would process: {slug} ({info['city']}, {info['county']} County)")
        return

    # Init Vertex
    log.info(f"Vertex AI init — project={GCP_PROJECT_ID}  model={GEMINI_MODEL}")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    model = GenerativeModel(GEMINI_MODEL)

    # Load existing results if any (allows resuming)
    results_file = OUTPUT_DIR / "attorneys.json"
    all_results: dict = {}
    if results_file.exists():
        try:
            all_results = json.loads(results_file.read_text(encoding="utf-8"))
            log.info(f"Loaded {len(all_results)} existing results — will skip already-done districts")
        except Exception:
            pass

    # ── SRO PHASE: scrape decisions index once ─────────────────────
    sro_by_district: dict[str, list[str]] = {slug: [] for slug in districts}

    if not args.skip_sro:
        log.info(f"Fetching SRO {args.year} decisions index...")
        sro_decisions = fetch_sro_decision_index(args.year)
        log.info(f"  Found {len(sro_decisions)} decision links")

        # Also try prior year for more coverage
        if args.year == 2024:
            prior = fetch_sro_decision_index(2023)
            sro_decisions.extend(prior)
            log.info(f"  + {len(prior)} from 2023 — total: {len(sro_decisions)}")

        # For each decision, check if it involves one of our districts
        checked = 0
        for dec in sro_decisions[:200]:  # cap at 200 to keep runtime reasonable
            time.sleep(SRO_DELAY)
            for slug, info in districts.items():
                result = extract_attorney_from_sro_html(dec["url"], info["sro_terms"])
                if result:
                    for atty in result["attorneys"]:
                        if atty not in sro_by_district[slug]:
                            sro_by_district[slug].append(atty)
                    log.info(f"  SRO hit: {slug} ← {result['attorneys']}")
            checked += 1
            if checked % 20 == 0:
                log.info(f"  Checked {checked}/{min(200, len(sro_decisions))} SRO decisions")

    # ── VERTEX PHASE: enrich each district ────────────────────────
    for slug, info in districts.items():
        if slug in all_results and all_results[slug].get("attorneys"):
            log.info(f"  SKIP {slug} — already in results")
            continue

        log.info(f"── {info['name']} ──────────────────────")
        known = sro_by_district.get(slug, [])
        if known:
            log.info(f"  SRO names to enrich: {known}")

        result = enrich_with_vertex(
            model,
            district_name=info["name"],
            city=info["city"],
            county=info["county"],
            known_names=known,
        )

        if result:
            all_results[slug] = result
            count = len(result.get("attorneys", []))
            log.info(f"  ✓ Found {count} attorney(s)")
        else:
            log.warning(f"  ✗ No results for {slug}")
            all_results[slug] = {"district": info["name"], "attorneys": [], "notes": "No results found"}

        # Save incrementally after each district so progress isn't lost
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results_file.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

        time.sleep(RATE_LIMIT_DELAY)

    # ── WRITE FINAL OUTPUTS ────────────────────────────────────────
    log.info("Writing outputs...")
    write_outputs(all_results)

    total_attorneys = sum(len(v.get("attorneys", [])) for v in all_results.values())
    high_conf = sum(
        1 for v in all_results.values()
        for a in v.get("attorneys", [])
        if a.get("confidence") == "high"
    )
    log.info("═" * 55)
    log.info(f"Districts processed : {len(all_results)}")
    log.info(f"Total attorneys     : {total_attorneys}")
    log.info(f"High confidence     : {high_conf}")
    log.info(f"Output directory    : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()