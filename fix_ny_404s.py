"""
fix_ny_404s.py
──────────────────────────────────────────────────────────────
Fixes all 404 issues found in the Feb 27 2026 site audit.

ISSUE SUMMARY (from Ahrefs CSV):
  PR=20, 507 inlinks  /terms   — footer link to nonexistent page
  PR=20, 507 inlinks  /shop    — footer link to nonexistent page (template leftover)
  PR=19, 492 inlinks  /districts/nyc-district-22-flatbush  — folder missing
  PR=19, 492 inlinks  /districts/nyc-district-24-corona    — folder missing
  PR=1,   20 inlinks  /districts/parent-advocacy-guide.html — bad relative link in D01
  PR=0,    3 inlinks  /districts/nyc-district-17-crown-Heights/  — mixed-case slug in href
  PR=0,    1 inlink   /districts/nyc-district-11-pelham-Parkway/ — mixed-case slug in href
  PR=0,    2 inlinks  /about/mission.html    — linked from /about but page missing
  PR=0,    2 inlinks  /about/methodology.html — linked from /about but page missing
  PR=0,    1 inlink   /districts/nyc-district-16-bed-Stuy/ — mixed-case slug in href
  PR=0,    1 inlink   /districts/nyc-district-02-upper-east-Side/ — mixed-case slug in href

FIXES APPLIED:
  FIX 1 — Create /terms.html stub page
  FIX 2 — Fix /shop links → /contact (or remove) in all HTML files
  FIX 3 — Build missing district folders (flatbush, corona) using Vertex AI
  FIX 4 — Fix bad /districts/parent-advocacy-guide.html relative link in D01 pages
  FIX 5 — Lowercase all mixed-case district slug hrefs across all HTML files
  FIX 6 — Create /about/mission.html and /about/methodology.html stub pages

SETUP:
  pip install google-cloud-aiplatform beautifulsoup4 lxml
  gcloud auth application-default login

USAGE:
  python fix_ny_404s.py                          # run all fixes
  python fix_ny_404s.py --dry-run               # preview only, no writes
  python fix_ny_404s.py --fix 1,2,5             # run specific fixes only
  python fix_ny_404s.py --skip 3               # skip Vertex district build
"""

import os, re, sys, json, time, argparse, logging
from pathlib import Path
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
SITE_ROOT      = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
DISTRICTS_DIR  = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\districts"
GCP_PROJECT_ID = "YOUR_GCP_PROJECT_ID"
GCP_REGION     = "us-central1"
GEMINI_MODEL   = "gemini-1.5-flash"
RATE_LIMIT_DELAY = 3
SITE_BASE_URL  = "https://www.newyorkspecialed.net"
ADVERTISE_URL  = "https://www.newyorkspecialed.net/contact"

# Mixed-case slugs found in hrefs that need to be lowercased
# Format: (bad_pattern, correct_slug)
MIXED_CASE_SLUGS = [
    ("nyc-district-17-crown-Heights", "nyc-district-17-crown-heights"),
    ("nyc-district-11-pelham-Parkway", "nyc-district-11-pelham-parkway"),
    ("nyc-district-16-bed-Stuy",       "nyc-district-16-bed-stuy"),
    ("nyc-district-02-upper-east-Side","nyc-district-02-upper-east-side"),
]

# Missing districts to build via Vertex
MISSING_DISTRICTS = {
    "nyc-district-22-flatbush": {
        "name":    "NYC District 22 — Flatbush",
        "type":    "urban",
        "city":    "Brooklyn",
        "county":  "Kings",
        "region":  "Brooklyn",
        "notes":   "Diverse Caribbean and Black community in Flatbush, Brooklyn. Evaluation delays reported. High proportion of multilingual families. Parents increasingly aware of IEP rights. Autism evaluations and speech therapy placements are frequent points of dispute.",
    },
    "nyc-district-24-corona": {
        "name":    "NYC District 24 — Corona / Jackson Heights",
        "type":    "urban",
        "city":    "Queens",
        "county":  "Queens",
        "region":  "Queens",
        "notes":   "One of the most linguistically diverse districts in the US. Large immigrant community — Spanish, Tibetan, Korean, Nepali, Bengali speakers. Bilingual special education services critically underprovided. High ELL rate. Families often unaware of IEP rights due to language barriers. Bilingual evaluations and interpreter access at CSE meetings are key issues.",
    },
}

# ──────────────────────────────────────────────
#  SHARED HTML COMPONENTS
# ──────────────────────────────────────────────
NATIONAL_RESOURCES = """
          <a class="free-card" href="https://www.wrightslaw.com" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-balance-scale"></i></div>
            <div class="free-card-text"><strong>Wrightslaw</strong>
              <span>Free guides on special education law, IEPs, and parent rights under IDEA.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>
          <a class="free-card" href="https://www.understood.org" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-brain"></i></div>
            <div class="free-card-text"><strong>Understood.org</strong>
              <span>Free expert guidance for parents of children with learning differences.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>"""

NY_STATE_RESOURCES = """
          <a class="free-card" href="https://www.nysed.gov/special-education" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-landmark"></i></div>
            <div class="free-card-text"><strong>NYSED Office of Special Education</strong>
              <span>NY State's official hub for special ed regulations, parent rights, and complaint filing.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>
          <a class="free-card" href="https://www.disabilityrightsny.org" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-gavel"></i></div>
            <div class="free-card-text"><strong>Disability Rights New York</strong>
              <span>Free legal advocacy for New Yorkers with disabilities.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>
          <a class="free-card" href="https://www.advocatesforchildren.org" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-child"></i></div>
            <div class="free-card-text"><strong>Advocates for Children of New York</strong>
              <span>Free legal representation for NYC students in special education disputes.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>"""


def std_header():
    return """<header class="site-header">
  <!-- standard NY header here -->
</header>"""

def std_footer():
    return """<footer class="site-footer">
  <!-- standard NY footer here -->
</footer>"""

def site_head(title, desc, canonical, extra_css=""):
    return f"""<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
  <meta name="description" content="{desc}"/>
  <link rel="canonical" href="{canonical}"/>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"/>
  <link href="/styles/global.css" rel="stylesheet"/>
  <link href="/styles/styles-nav-footer.css" rel="stylesheet"/>{extra_css}
</head>"""


# ──────────────────────────────────────────────
#  FIX 1: Create /terms.html
# ──────────────────────────────────────────────
def fix_1_create_terms(dry_run: bool):
    log.info("FIX 1 ── Creating /terms.html")
    terms_path = Path(SITE_ROOT) / "terms.html"

    if terms_path.exists():
        log.info("  SKIP — terms.html already exists")
        return

    html = f"""<!DOCTYPE html>
<html lang="en">
{site_head(
    "Terms of Service | NY Special Ed",
    "Terms of service for New York Special Ed — an independent parent resource for navigating the special education system in New York State.",
    f"{SITE_BASE_URL}/terms"
)}
<body>
<!-- ny-terms-v1 -->
{std_header()}

<section class="page-hero-dark">
  <div class="container">
    <h1>Terms of Service</h1>
    <p class="hero-sub">Please read these terms before using NY Special Ed.</p>
  </div>
</section>

<main>
  <div class="container" style="max-width:760px; padding:48px 24px;">

    <p style="color:#666; margin-bottom:32px;"><em>Last updated: February 2026</em></p>

    <div class="content-section">
      <h2>1. About This Site</h2>
      <p>NY Special Ed (<strong>newyorkspecialed.net</strong>) is an independent informational resource for parents of children receiving special education services in New York State. This site is not affiliated with, endorsed by, or operated by the New York State Education Department (NYSED), any school district, or any government agency.</p>
    </div>

    <div class="content-section">
      <h2>2. Not Legal Advice</h2>
      <p>Nothing on this website constitutes legal advice. The information provided is for general educational purposes only. For advice specific to your child's situation, consult a qualified special education attorney or advocate licensed in New York State.</p>
    </div>

    <div class="content-section">
      <h2>3. Accuracy of Information</h2>
      <p>We make every effort to keep information current and accurate, but special education law and district policies change. Always verify critical information with NYSED, your district's CSE office, or a qualified professional before taking action.</p>
    </div>

    <div class="content-section">
      <h2>4. Third-Party Providers</h2>
      <p>Some pages on this site list attorneys, advocates, and evaluators who have paid for placement. Listing does not constitute endorsement. We do not verify credentials, licensure, or outcomes. Always independently verify any provider's qualifications before engaging their services.</p>
    </div>

    <div class="content-section">
      <h2>5. External Links</h2>
      <p>We link to external websites for convenience. We are not responsible for the content, accuracy, or privacy practices of external sites.</p>
    </div>

    <div class="content-section">
      <h2>6. Limitation of Liability</h2>
      <p>NY Special Ed and its operators shall not be liable for any damages arising from your use of, or inability to use, this website or any information contained herein.</p>
    </div>

    <div class="content-section">
      <h2>7. Changes to These Terms</h2>
      <p>We may update these terms at any time. Continued use of the site constitutes acceptance of any updated terms.</p>
    </div>

    <div class="content-section">
      <h2>8. Contact</h2>
      <p>Questions about these terms? <a href="/contact">Contact us here</a>.</p>
    </div>

  </div>
</main>

{std_footer()}
</body>
</html>"""

    if dry_run:
        log.info("  [DRY RUN] Would create: terms.html")
    else:
        terms_path.write_text(html, encoding="utf-8")
        log.info(f"  ✓ Created: {terms_path}")


# ──────────────────────────────────────────────
#  FIX 2: Fix /shop links → /contact
# ──────────────────────────────────────────────
def fix_2_remove_shop_links(dry_run: bool):
    """
    Scans every HTML file for href="/shop" or href="shop" and rewrites to /contact.
    Also handles href containing 'shop' in footer/nav context.
    """
    log.info("FIX 2 ── Replacing /shop links with /contact across all HTML files")
    site_root = Path(SITE_ROOT)
    files_changed = 0
    links_fixed = 0

    for html_file in site_root.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="replace")

        # Match href="/shop", href="/shop/", href="shop", href="shop/"
        # but NOT href="/shopping-cart" or similar
        pattern = r'href=["\']/?shop/?["\']'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if not matches:
            continue

        new_text = re.sub(pattern, 'href="/contact"', text, flags=re.IGNORECASE)
        count = len(matches)
        links_fixed += count

        if dry_run:
            log.info(f"  [DRY RUN] {html_file.relative_to(site_root)} — would fix {count} /shop link(s)")
        else:
            html_file.write_text(new_text, encoding="utf-8")
            log.info(f"  ✓ Fixed {count} /shop link(s) in {html_file.relative_to(site_root)}")
            files_changed += 1

    if links_fixed == 0:
        log.info("  No /shop links found — may already be fixed or in a template file")
    else:
        log.info(f"  Total: {links_fixed} /shop links fixed across {files_changed} files")


# ──────────────────────────────────────────────
#  FIX 3: Build missing district folders via Vertex
# ──────────────────────────────────────────────
def fix_3_build_missing_districts(dry_run: bool):
    log.info("FIX 3 ── Building missing district folders: flatbush, corona")

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
    except ImportError:
        log.error("  google-cloud-aiplatform not installed. Run: pip install google-cloud-aiplatform")
        return

    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    model = GenerativeModel(GEMINI_MODEL)

    for slug, info in MISSING_DISTRICTS.items():
        _build_district_pages(slug, info, model, dry_run)


def _build_district_pages(slug: str, info: dict, model, dry_run: bool):
    """Generate all standard pages for a new NYC district."""
    from vertexai.generative_models import GenerativeModel

    folder = Path(DISTRICTS_DIR) / slug
    log.info(f"  Building: {info['name']} → {folder}")

    if not dry_run:
        folder.mkdir(parents=True, exist_ok=True)

    pages = [
        ("index.html",               "<!-- ny-index-v1 -->",    _prompt_district_index,   _render_index),
        ("cse-meeting-guide.html",   "<!-- ny-cse-guide-v1 -->",_prompt_cse_guide,        _render_content_page),
        ("evaluation-process.html",  "<!-- ny-eval-v1 -->",     _prompt_eval,             _render_content_page),
        ("discipline-rights.html",   "<!-- ny-disc-v1 -->",     _prompt_discipline,       _render_content_page),
        ("leadership-directory.html","<!-- ny-directory-v1 -->",_prompt_directory,        _render_directory),
        ("special-ed-updates.html",  "<!-- ny-updates-v1 -->",  _prompt_updates,          _render_updates),
        ("partners.html",            "<!-- ny-partners-rebuilt-v1 -->", _prompt_partners,  _render_partners),
        ("parent-advocacy-guide.html","<!-- ny-advocacy-guide-v1 -->",  _prompt_guide,    _render_guide),
    ]

    for filename, marker, prompt_fn, render_fn in pages:
        filepath = folder / filename
        if filepath.exists() and marker in filepath.read_text(encoding="utf-8", errors="replace"):
            log.info(f"    SKIP {filename} — already built")
            continue

        log.info(f"    Generating {filename}...")
        prompt = prompt_fn(slug, info)
        data = _call_vertex(model, prompt, filename)
        if not data:
            continue

        html = render_fn(slug, info, filename, marker, data)

        if dry_run:
            log.info(f"    [DRY RUN] Would write {filename} ({len(html):,} chars)")
        else:
            filepath.write_text(html, encoding="utf-8")
            log.info(f"    ✓ {filename}")

        time.sleep(RATE_LIMIT_DELAY)


def _call_vertex(model, prompt: str, label: str):
    import re as _re, json as _json
    try:
        resp = model.generate_content(prompt)
        raw  = resp.text.strip()
        raw  = _re.sub(r"^```json\s*", "", raw, flags=_re.MULTILINE)
        raw  = _re.sub(r"^```\s*",     "", raw, flags=_re.MULTILINE)
        raw  = _re.sub(r"\s*```$",     "", raw.strip())
        return _json.loads(raw)
    except Exception as e:
        log.error(f"    Vertex ERROR ({label}): {e}")
        return None


def _silo_nav(name: str, slug: str, active: str) -> str:
    pages = [
        ("index",    "index.html",                 "District Home"),
        ("cse",      "cse-meeting-guide.html",      "CSE Guide"),
        ("eval",     "evaluation-process.html",     "Evaluations"),
        ("disc",     "discipline-rights.html",      "Discipline Rights"),
        ("contacts", "leadership-directory.html",   "Contacts"),
        ("updates",  "special-ed-updates.html",     "Updates"),
        ("partners", "partners.html",               "Providers &amp; Support"),
        ("guide",    "parent-advocacy-guide.html",  "Advocacy Guide"),
    ]
    links = "".join(
        f'<a href="{href}"{" class=\"active\"" if k==active else ""}>{label}</a>\n      '
        for k, href, label in pages
    )
    return f"""<nav class="silo-nav" aria-label="District pages">
      <strong>{name} Resources:</strong>
      {links}
    </nav>"""


def _trust():
    return """<div class="trust-anchor">
      <strong>Hi, I'm a New York parent of a child with an IEP.</strong>
      When I watched the system fail my child, I realized how broken the CSE process is.
      I built this resource to help parents like you get the services your child deserves. You are not alone.
    </div>
    <hr class="divider" style="margin:8px 0 40px;"/>"""


# ── Prompts ──────────────────────────────────

def _prompt_district_index(slug, info):
    return f"""You are writing content for a New York special education parent resource website.
District: {info['name']} | City: {info['city']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY raw JSON. No markdown. Keys:
{{
  "meta_description": "...",
  "hero_sub": "...",
  "intro_h2": "...",
  "intro_p": "...",
  "local_note": "...",
  "quick_stats": [{{"label":"...","value":"..."}}, {{"label":"...","value":"..."}}, {{"label":"...","value":"..."}}],
  "hub_cards": [
    {{"icon":"fas fa-...","title":"...","desc":"...","href":"cse-meeting-guide.html","cta":"..."}},
    {{"icon":"fas fa-...","title":"...","desc":"...","href":"evaluation-process.html","cta":"..."}},
    {{"icon":"fas fa-...","title":"...","desc":"...","href":"discipline-rights.html","cta":"..."}},
    {{"icon":"fas fa-...","title":"...","desc":"...","href":"partners.html","cta":"..."}}
  ]
}}
meta_description: 140-160 chars. Mention {info['name']}, CSE, parent rights. Don't start with "Find".
hero_sub: 1 sentence acknowledging difficulty of CSE process in {info['name']}.
intro_h2: 6-10 words.
intro_p: 2-3 sentences, warm, mention {info['county']} County and NY CSE process.
local_note: 1-2 specific sentences about special ed challenges specific to {info['name']} or {info['city']}.
quick_stats: 3 real/representative stats about {info['name']} special education (IEP rate, enrollment, etc).
hub_cards: 4 cards with exact hrefs listed above. icon=Font Awesome 6 solid class. title=3-5 words. desc=10-15 words. cta=2-4 words.
"""


def _prompt_cse_guide(slug, info):
    return f"""Write a CSE meeting guide for NY special ed parents in {info['name']}, {info['city']}.
Context: {info['notes']}
Return ONLY raw JSON:
{{
  "meta_description":"...",
  "hero_sub":"...",
  "intro_p":"...",
  "sections":[{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}}],
  "faq":[{{"q":"...","a":"..."}},{{"q":"...","a":"..."}},{{"q":"...","a":"..."}}],
  "checklist":["...","...","...","...","..."]
}}
meta_description: 140-160 chars with {info['name']}, CSE meeting, parent rights.
hero_sub: 1 sentence about what parents can do before their CSE meeting.
intro_p: 2-3 sentences, warm, mention {info['name']} specifically.
sections: 4 sections covering (1) what to expect at the meeting (2) how to prepare (3) your rights at the meeting (4) after the meeting. content_html uses only <p><ul><li><strong><ol>.
faq: 3 real questions a {info['name']} parent would Google. Mention district in ≥2 answers. Use NY rules (60-school-day eval, Part 200).
checklist: 5 action items to do before a CSE meeting. Short, imperative sentences.
"""


def _prompt_eval(slug, info):
    return f"""Write an evaluation rights page for NY special ed parents in {info['name']}.
Context: {info['notes']}
Return ONLY raw JSON:
{{
  "meta_description":"...",
  "hero_sub":"...",
  "intro_p":"...",
  "sections":[{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}}],
  "faq":[{{"q":"...","a":"..."}},{{"q":"...","a":"..."}},{{"q":"...","a":"..."}}]
}}
meta_description: 140-160 chars with {info['name']}, evaluation, IEE. No "Find".
hero_sub: 1 sentence about requesting evaluations in {info['name']}.
sections: 4 sections — (1) how to request a district evaluation (2) 60-school-day NY timeline rule (3) IEE rights at district expense (4) types of evaluations to request.
faq: 3 questions. ≥1 about IEEs, ≥1 about timelines. Mention {info['name']} in ≥2. NY law only (Part 200, no Texas/ARD).
"""


def _prompt_discipline(slug, info):
    return f"""Write a discipline rights page for NY special ed parents in {info['name']}.
Context: {info['notes']}
Return ONLY raw JSON:
{{
  "meta_description":"...",
  "hero_sub":"...",
  "intro_p":"...",
  "sections":[{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}}],
  "faq":[{{"q":"...","a":"..."}},{{"q":"...","a":"..."}},{{"q":"...","a":"..."}}],
  "warning_signs":["...","...","...","..."]
}}
meta_description: 140-160 chars with {info['name']}, suspension, IEP discipline. No "Find".
sections: (1) 10-day rule and MDR trigger (2) what happens at MDR (3) if behavior IS manifestation (4) impartial hearing process. NY terminology: IHO, NYSED complaint, Part 200.
faq: 3 questions, ≥1 about MDR, ≥1 about impartial hearings. Mention {info['name']} in ≥2.
warning_signs: 4 short phrases — situations requiring immediate legal help.
"""


def _prompt_directory(slug, info):
    return f"""Write a special education contacts page for {info['name']}, NY.
Return ONLY raw JSON:
{{
  "meta_description":"...",
  "hero_sub":"...",
  "intro_p":"...",
  "key_contacts":[{{"role":"...","note":"..."}},{{"role":"...","note":"..."}},{{"role":"...","note":"..."}},{{"role":"...","note":"..."}},{{"role":"...","note":"..."}}],
  "how_to_p":"...",
  "nysed_complaint_p":"..."
}}
5 roles relevant to NYC special ed (CSE Chairperson, Director of Special Education, etc). note=when/why parent contacts them.
how_to_p: practical advice on reaching district staff (written requests, recordkeeping).
nysed_complaint_p: 1-2 sentences about filing NYSED State complaint if district is unresponsive.
"""


def _prompt_updates(slug, info):
    return f"""Write a special education updates/news page for {info['name']}, NY.
Context: {info['notes']}
Return ONLY raw JSON:
{{
  "meta_description":"...",
  "hero_sub":"...",
  "intro_p":"...",
  "why_track_h2":"...",
  "why_track_p":"...",
  "things_to_track":["...","...","...","...","..."],
  "official_sources":[{{"name":"...","url":"https://...","desc":"..."}},{{"name":"...","url":"https://...","desc":"..."}}],
  "cta_p":"..."
}}
official_sources: 2 REAL URLs. For NYC districts use nyc.gov/schools or schools.nyc.gov resources. Second source: NYSED or borough-specific resource.
"""


def _prompt_partners(slug, info):
    return f"""Write a providers/partners page for {info['name']} special ed parents in {info['city']}, NY.
Context: {info['notes']}
Return ONLY raw JSON:
{{
  "meta_description":"...",
  "insight_h4":"...",
  "insight_p":"...",
  "process_items":[{{"h4":"...","p":"..."}},{{"h4":"...","p":"..."}},{{"h4":"...","p":"..."}}],
  "local_resources":[{{"icon":"fas fa-...","name":"...","url":"https://...","desc":"..."}},{{"icon":"fas fa-...","name":"...","url":"https://...","desc":"..."}}]
}}
insight_h4: 6-10 words mentioning {info['name']}.
insight_p: 2-3 sentences about support available. Urban NYC focus: bilingual evals, ELL rights, autism.
process_items: 3 items. h4=3-5 words. p=max 15 words. Urban: evaluation delays, bilingual CSE rights, MDR issues.
local_resources: 2 REAL NYC organizations with working URLs serving {info['city']} area.
  Options: Brooklyn Arc, Queens Arc, INCLUDEnyc, Make a Wave NY, Caribbean Equality Project (for Flatbush), 
  Chhaya CDC (for Corona/Jackson Heights), Queens Community House, HANAC Inc.
  Do NOT include DRNY, Advocates for Children, NYSED (already in template).
"""


def _prompt_guide(slug, info):
    return f"""Write a parent advocacy guide for {info['name']} special ed parents.
Context: {info['notes']}
Return ONLY raw JSON:
{{
  "meta_title":"...",
  "meta_description":"...",
  "intro_p":"...",
  "sections":[{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}},{{"h2":"...","content_html":"..."}}],
  "faq":[{{"q":"...","a":"..."}},{{"q":"...","a":"..."}},{{"q":"...","a":"..."}},{{"q":"...","a":"..."}}],
  "cta_p":"..."
}}
meta_title: max 60 chars. Format: "CSE Advocacy Guide for {info['name']} Parents | NY Special Ed"
sections: (1) local CSE process specifics (2) building your case (3) advocating at the table (4) when to escalate.
faq: 4 questions. Mention {info['name']} in ≥3. Cover: eval timelines, IEE, dispute process, local resources. NY law only.
cta_p: 1-2 sentences transitioning to partners.html.
"""


# ── Renderers ────────────────────────────────

def _render_index(slug, info, filename, marker, data):
    name = info['name']
    silo = _silo_nav(name, slug, "index")
    canonical = f"{SITE_BASE_URL}/districts/{slug}/index.html"

    cards_html = ""
    for c in data.get("hub_cards", []):
        cards_html += f"""      <a class="hub-card" href="{c['href']}">
        <div class="hub-card-icon"><i class="{c['icon']}"></i></div>
        <div class="hub-card-body">
          <h3>{c['title']}</h3>
          <p>{c['desc']}</p>
          <span class="hub-card-cta">{c['cta']} &rarr;</span>
        </div>
      </a>\n"""

    stats_html = "".join(
        f'        <div class="stat-item"><div class="stat-value">{s["value"]}</div><div class="stat-label">{s["label"]}</div></div>\n'
        for s in data.get("quick_stats", [])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
{site_head(f"Special Education Resources — {name} | NY Special Ed", data['meta_description'], canonical)}
<body>
{marker}
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{name}</span>
    <h1>Special Education Resources<br/>in {name}</h1>
    <p class="hero-sub">{data['hero_sub']}</p>
  </div>
</section>
<main>
  <div class="container">
    {silo}
    {_trust()}
    <div class="district-intro">
      <h2>{data.get('intro_h2','')}</h2>
      <p>{data.get('intro_p','')}</p>
    </div>
    <div class="quick-stats-bar">
{stats_html}    </div>
    <div class="insight-box" style="margin-bottom:40px;">
      <div class="insight-icon"><i class="fas fa-map-marker-alt"></i></div>
      <div class="insight-text">
        <h4>About Special Ed in {name}</h4>
        <p>{data.get('local_note','')}</p>
      </div>
    </div>
    <div class="section-title-row"><h2>What Do You Need Help With?</h2></div>
    <div class="hub-grid">
{cards_html}      <a class="hub-card" href="parent-advocacy-guide.html">
        <div class="hub-card-icon"><i class="fas fa-book-open-reader"></i></div>
        <div class="hub-card-body">
          <h3>Advocacy Guide</h3>
          <p>Step-by-step strategies for advocating at the CSE table in {name}.</p>
          <span class="hub-card-cta">Read the guide &rarr;</span>
        </div>
      </a>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def _render_content_page(slug, info, filename, marker, data):
    """Generic renderer for CSE, eval, discipline pages."""
    name = info['name']
    page_map = {
        "cse-meeting-guide.html":   ("cse",  f"CSE Meeting Guide<br/>for {name} Parents",    f"CSE Meeting Guide — {name} | NY Special Ed"),
        "evaluation-process.html":  ("eval", f"Requesting an Evaluation<br/>in {name}",       f"Evaluation Rights — {name} | NY Special Ed"),
        "discipline-rights.html":   ("disc", f"Discipline Rights &amp; Impartial Hearings<br/>in {name}", f"Discipline Rights — {name} | NY Special Ed"),
    }
    active_key, h1, page_title = page_map.get(filename, ("index", name, name))
    silo     = _silo_nav(name, slug, active_key)
    canonical = f"{SITE_BASE_URL}/districts/{slug}/{filename}"

    sections_html = "".join(
        f'<div class="content-section"><h2>{s["h2"]}</h2>{s["content_html"]}</div>'
        for s in data.get("sections", [])
    )

    faq_html = "".join(
        f'<div class="faq-item"><h3>{q["q"]}</h3><p>{q["a"]}</p></div>'
        for q in data.get("faq", [])
    )

    # Extra elements
    extra = ""
    if filename == "cse-meeting-guide.html" and data.get("checklist"):
        items = "".join(f"<li>{i}</li>" for i in data["checklist"])
        extra = f'<div class="content-section checklist-section"><h2>Before Your CSE Meeting — Checklist</h2><ul class="checklist">{items}</ul></div>'
    elif filename == "discipline-rights.html" and data.get("warning_signs"):
        items = "".join(f"<li>{w}</li>" for w in data["warning_signs"])
        extra = f'<div class="content-section warning-section"><h2>When to Get Legal Help Immediately</h2><ul class="warning-list">{items}</ul><p><a href="partners.html">Find a special education attorney in {name} &rarr;</a></p></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
{site_head(page_title, data['meta_description'], canonical)}
<body>
{marker}
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{name}</span>
    <h1>{h1}</h1>
    <p class="hero-sub">{data.get('hero_sub','')}</p>
  </div>
</section>
<main>
  <div class="container">
    {silo}
    {_trust()}
    <div class="content-intro"><p>{data.get('intro_p','')}</p></div>
    {sections_html}
    {extra}
    <div class="faq-section" style="margin-top:48px;">
      <div class="section-title-row">
        <h2>Frequently Asked Questions</h2>
        <span>{name} parents ask</span>
      </div>
      {faq_html}
    </div>
    <div class="insight-box" style="margin-top:40px;">
      <div class="insight-icon"><i class="fas fa-hands-helping"></i></div>
      <div class="insight-text">
        <h4>Need local help?</h4>
        <p>Browse attorneys, advocates, and evaluators serving {name}. <a href="partners.html">Find local providers &rarr;</a></p>
      </div>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def _render_directory(slug, info, filename, marker, data):
    name = info['name']
    silo = _silo_nav(name, slug, "contacts")
    canonical = f"{SITE_BASE_URL}/districts/{slug}/leadership-directory.html"
    contacts_html = "".join(
        f'<div class="contact-card"><div class="contact-role"><i class="fas fa-user-tie"></i> {c["role"]}</div><div class="contact-note">{c["note"]}</div></div>'
        for c in data.get("key_contacts", [])
    )
    return f"""<!DOCTYPE html>
<html lang="en">
{site_head(f"Special Education Contacts — {name} | NY Special Ed", data['meta_description'], canonical)}
<body>
{marker}
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{name}</span>
    <h1>Special Education Contacts<br/>in {name}</h1>
    <p class="hero-sub">{data.get('hero_sub','')}</p>
  </div>
</section>
<main>
  <div class="container">
    {silo}
    {_trust()}
    <div class="content-intro"><p>{data.get('intro_p','')}</p></div>
    <div class="section-title-row"><h2>Key Roles in {name}'s Special Education Department</h2></div>
    <div class="contact-grid">{contacts_html}</div>
    <div class="content-section">
      <h2>How to Reach District Staff Effectively</h2>
      <p>{data.get('how_to_p','')}</p>
    </div>
    <div class="content-section">
      <h2>When the District Doesn't Respond — NYSED Complaints</h2>
      <p>{data.get('nysed_complaint_p','')}</p>
      <p><a href="https://www.nysed.gov/special-education/state-complaints" target="_blank" rel="noopener">File a State Complaint with NYSED &rarr;</a></p>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def _render_updates(slug, info, filename, marker, data):
    name = info['name']
    silo = _silo_nav(name, slug, "updates")
    canonical = f"{SITE_BASE_URL}/districts/{slug}/special-ed-updates.html"
    track_items = "".join(f"<li>{t}</li>" for t in data.get("things_to_track", []))
    sources_html = "".join(
        f'<a class="free-card" href="{s["url"]}" target="_blank" rel="noopener"><div class="free-card-icon"><i class="fas fa-external-link-alt"></i></div><div class="free-card-text"><strong>{s["name"]}</strong><span>{s["desc"]}</span></div></a>'
        for s in data.get("official_sources", [])
    )
    return f"""<!DOCTYPE html>
<html lang="en">
{site_head(f"Special Education Updates — {name} | NY Special Ed", data['meta_description'], canonical)}
<body>
{marker}
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{name}</span>
    <h1>Special Education Updates<br/>in {name}</h1>
    <p class="hero-sub">{data.get('hero_sub','')}</p>
  </div>
</section>
<main>
  <div class="container">
    {silo}
    {_trust()}
    <div class="content-intro"><p>{data.get('intro_p','')}</p></div>
    <div class="content-section">
      <h2>{data.get('why_track_h2','Why Staying Informed Matters')}</h2>
      <p>{data.get('why_track_p','')}</p>
    </div>
    <div class="content-section">
      <h2>What to Monitor in {name}</h2>
      <ul>{track_items}</ul>
    </div>
    <div class="content-section">
      <h2>Official Sources</h2>
      <div class="free-cards-grid">{sources_html}</div>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def _render_partners(slug, info, filename, marker, data):
    name = info['name']
    silo = _silo_nav(name, slug, "partners")
    canonical = f"{SITE_BASE_URL}/districts/{slug}/partners.html"

    proc_html = "".join(
        f'<div class="process-item"><div class="process-num">{i}</div><div class="process-body"><h4>{item["h4"]}</h4><p>{item["p"]}</p></div></div>'
        for i, item in enumerate(data.get("process_items", []), 1)
    )
    local_html = "".join(
        f'<a class="free-card" href="{r["url"]}" target="_blank" rel="noopener"><div class="free-card-icon"><i class="{r["icon"]}"></i></div><div class="free-card-text"><strong>{r["name"]}</strong><span>{r["desc"]}</span></div><i class="fas fa-external-link-alt free-card-arrow"></i></a>'
        for r in data.get("local_resources", [])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
{site_head(f"Special Education Providers — {name} | NY Special Ed", data['meta_description'], canonical,
           extra_css='\n  <link href="/styles/partners.css" rel="stylesheet"/>')}
<body>
{marker}
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{name}</span>
    <h1>Special Education Providers<br/>in {name}</h1>
    <p class="hero-sub">Connect with local advocates, attorneys, and evaluators who know the CSE process in {name} specifically.</p>
  </div>
</section>
<main>
  <div class="container">
    {silo}
    {_trust()}
    <div class="featured-ad-zone">
      <span class="ad-badge-premium">District Exclusive</span>
      <div class="ad-logo-box"><i class="fas fa-building"></i><span>Your Logo</span></div>
      <div class="ad-content">
        <span class="label label-gold">Featured Partner</span>
        <h3>Be the trusted authority for {name} families</h3>
        <p>Reach high-intent parents seeking evaluations, advocacy, or legal help — at the moment they need it most.</p>
        <div class="ad-tags">
          <span class="ad-tag">IEE Evaluations</span>
          <span class="ad-tag">CSE Advocacy</span>
          <span class="ad-tag">Bilingual Services</span>
          <span class="ad-tag">Legal Support</span>
        </div>
      </div>
      <a class="btn-claim" href="{ADVERTISE_URL}">Reserve This Spot <i class="fas fa-arrow-right" style="font-size:.75rem;"></i></a>
    </div>
    <div class="insight-box">
      <div class="insight-icon"><i class="fas fa-lightbulb"></i></div>
      <div class="insight-text">
        <h4>{data.get('insight_h4','')}</h4>
        <p>{data.get('insight_p','')}</p>
      </div>
    </div>
    <div class="section-title-row">
      <h2>Navigating Special Ed in {name}</h2>
      <span>Key rights — <a href="parent-advocacy-guide.html">full guide &rarr;</a></span>
    </div>
    <div class="process-strip">{proc_html}</div>
    <div class="section-title-row mt-56"><h2>Advocates &amp; CSE Support</h2></div>
    <div class="ad-slot-card">
      <div class="ad-slot-logo"><i class="fas fa-user-tie fa-lg"></i></div>
      <div class="ad-slot-content"><h4>Your Advocacy Firm</h4><p>Be the first advocate parents call when they hit a wall at the CSE table in {name}.</p></div>
      <a href="{ADVERTISE_URL}" class="ad-slot-cta">Claim this listing</a>
    </div>
    <div class="section-title-row mt-48"><h2>Special Education Attorneys</h2></div>
    <div class="ad-slot-card">
      <div class="ad-slot-logo"><i class="fas fa-scale-balanced fa-lg"></i></div>
      <div class="ad-slot-content"><h4>Your Law Firm</h4><p>Position your firm as the go-to legal resource for {name} families.</p></div>
      <a href="{ADVERTISE_URL}" class="ad-slot-cta">Claim this listing</a>
    </div>
    <div class="section-title-row mt-48"><h2>Independent Evaluators</h2></div>
    <div class="ad-slot-card">
      <div class="ad-slot-logo"><i class="fas fa-brain fa-lg"></i></div>
      <div class="ad-slot-content"><h4>Your Evaluation Practice</h4><p>Reach {name} parents seeking an independent neuropsychological evaluation.</p></div>
      <a href="{ADVERTISE_URL}" class="ad-slot-cta">Claim this listing</a>
    </div>
  </div>
  <div class="container">
    <section class="free-resources-section">
      <div class="free-resources-intro">
        <span class="label label-green">No cost to families</span>
        <h2>Free &amp; Non-Profit Resources</h2>
      </div>
      <div class="resource-tier tier-national">
        <div class="tier-header"><i class="fas fa-flag-usa"></i> National</div>
        <div class="tier-body">{NATIONAL_RESOURCES}</div>
      </div>
      <div class="resource-tier tier-state">
        <div class="tier-header"><i class="fas fa-star"></i> New York State</div>
        <div class="tier-body">{NY_STATE_RESOURCES}</div>
      </div>
      <div class="resource-tier tier-local">
        <div class="tier-header"><i class="fas fa-map-marker-alt"></i> Local — {name} Area</div>
        <div class="tier-body">{local_html}</div>
      </div>
    </section>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def _render_guide(slug, info, filename, marker, data):
    name = info['name']
    silo = _silo_nav(name, slug, "guide")
    canonical = f"{SITE_BASE_URL}/districts/{slug}/parent-advocacy-guide.html"
    sections_html = "".join(
        f'<div class="content-section"><h2>{s["h2"]}</h2>{s["content_html"]}</div>'
        for s in data.get("sections", [])
    )
    faq_html = "".join(
        f'<div class="faq-item"><h3>{q["q"]}</h3><p>{q["a"]}</p></div>'
        for q in data.get("faq", [])
    )
    meta_title = data.get("meta_title", f"CSE Advocacy Guide — {name} | NY Special Ed")
    return f"""<!DOCTYPE html>
<html lang="en">
{site_head(meta_title, data['meta_description'], canonical)}
<body>
{marker}
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{name}</span>
    <h1>Parent Advocacy Guide<br/>for {name}</h1>
    <p class="hero-sub">Practical strategies for navigating the CSE process and advocating for your child in {name}.</p>
  </div>
</section>
<main>
  <div class="container">
    {silo}
    {_trust()}
    <div class="content-intro"><p>{data.get('intro_p','')}</p></div>
    {sections_html}
    <div class="faq-section" style="margin-top:48px;">
      <div class="section-title-row"><h2>Frequently Asked Questions</h2><span>{name} parents ask</span></div>
      {faq_html}
    </div>
    <div class="insight-box" style="margin-top:48px;">
      <div class="insight-icon"><i class="fas fa-hands-helping"></i></div>
      <div class="insight-text">
        <h4>Need a local advocate or evaluator?</h4>
        <p>{data.get('cta_p','')} <a href="partners.html">Browse local providers in {name} &rarr;</a></p>
      </div>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


# ──────────────────────────────────────────────
#  FIX 4: Fix /districts/parent-advocacy-guide.html bad relative link
# ──────────────────────────────────────────────
def fix_4_bad_guide_link(dry_run: bool):
    """
    District 01 Lower East Side pages have a link pointing to
    ../parent-advocacy-guide.html  (resolves to /districts/parent-advocacy-guide.html — 404)
    Correct path is just parent-advocacy-guide.html (same folder).
    """
    log.info("FIX 4 ── Fixing bad ../parent-advocacy-guide.html relative links")
    d01_folder = Path(DISTRICTS_DIR) / "nyc-district-01-lower-east-side"

    if not d01_folder.exists():
        log.warning(f"  Folder not found: {d01_folder}")
        return

    fixed_count = 0
    for html_file in d01_folder.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        # Match any href that resolves to ../parent-advocacy-guide.html
        if "../parent-advocacy-guide.html" not in text:
            continue

        new_text = text.replace("../parent-advocacy-guide.html", "parent-advocacy-guide.html")
        fixed_count += 1

        if dry_run:
            log.info(f"  [DRY RUN] Would fix: {html_file.name}")
        else:
            html_file.write_text(new_text, encoding="utf-8")
            log.info(f"  ✓ Fixed: {html_file.name}")

    if fixed_count == 0:
        log.info("  No ../parent-advocacy-guide.html links found in District 01 pages")
    else:
        log.info(f"  Fixed {fixed_count} file(s) in nyc-district-01-lower-east-side")


# ──────────────────────────────────────────────
#  FIX 5: Fix mixed-case district slug hrefs
# ──────────────────────────────────────────────
def fix_5_lowercase_slugs(dry_run: bool):
    """
    Internal links like href="/districts/nyc-district-17-crown-Heights/index.html"
    need to be lowercased so they resolve correctly on case-sensitive servers.
    Scans ALL html files site-wide.
    """
    log.info("FIX 5 ── Lowercasing mixed-case district slugs in all HTML hrefs/srcs")
    site_root = Path(SITE_ROOT)
    total_fixes = 0
    files_changed = 0

    for html_file in site_root.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        new_text = text
        file_fixes = 0

        for bad_slug, correct_slug in MIXED_CASE_SLUGS:
            if bad_slug in new_text:
                new_text = new_text.replace(bad_slug, correct_slug)
                count = text.count(bad_slug)
                file_fixes += count
                log.debug(f"    {html_file.name}: {bad_slug} → {correct_slug} ({count}×)")

        if file_fixes > 0:
            total_fixes += file_fixes
            files_changed += 1
            rel = html_file.relative_to(site_root)
            if dry_run:
                log.info(f"  [DRY RUN] {rel} — would fix {file_fixes} mixed-case slug(s)")
            else:
                html_file.write_text(new_text, encoding="utf-8")
                log.info(f"  ✓ Fixed {file_fixes} slug(s) in {rel}")

    if total_fixes == 0:
        log.info("  No mixed-case slugs found — may already be fixed")
    else:
        log.info(f"  Total: {total_fixes} slug fixes across {files_changed} files")


# ──────────────────────────────────────────────
#  FIX 6: Create /about/mission.html and /about/methodology.html
# ──────────────────────────────────────────────
def fix_6_create_about_pages(dry_run: bool):
    log.info("FIX 6 ── Creating /about/mission.html and /about/methodology.html")
    about_dir = Path(SITE_ROOT) / "about"

    if not about_dir.exists():
        if dry_run:
            log.info("  [DRY RUN] Would create /about/ directory")
        else:
            about_dir.mkdir(parents=True)
            log.info(f"  Created directory: {about_dir}")

    # --- mission.html ---
    mission_path = about_dir / "mission.html"
    if mission_path.exists():
        log.info("  SKIP mission.html — already exists")
    else:
        mission_html = f"""<!DOCTYPE html>
<html lang="en">
{site_head(
    "Our Mission | NY Special Ed",
    "NY Special Ed exists to give New York parents the information, tools, and local resources they need to advocate effectively for their child's special education rights.",
    f"{SITE_BASE_URL}/about/mission"
)}
<body>
<!-- ny-mission-v1 -->
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <h1>Our Mission</h1>
    <p class="hero-sub">Why we built this — and who we built it for.</p>
  </div>
</section>
<main>
  <div class="container" style="max-width:760px; padding:48px 24px;">

    <div class="trust-anchor">
      <strong>Hi, I'm a New York parent of a child with an IEP.</strong>
      When I watched the system fail my child, I realized how broken the CSE process is.
      I built this resource to help parents like you get the services your child deserves. You are not alone.
    </div>
    <hr class="divider" style="margin:8px 0 40px;"/>

    <div class="content-section">
      <h2>Why This Site Exists</h2>
      <p>New York's special education system is complex, fragmented, and often hostile to the parents it's supposed to serve. Every district has a CSE. Every CSE has lawyers. Most parents walk in alone.</p>
      <p>NY Special Ed was built to change that balance — even a little. By giving parents clear, district-specific information about their rights under the IDEA and New York State's Part 200 regulations, we aim to level a playing field that has been tilted against families for too long.</p>
    </div>

    <div class="content-section">
      <h2>What We Do</h2>
      <p>We maintain independent resource pages for every significant school district in New York State. Each district page covers:</p>
      <ul>
        <li>How to request an evaluation and what happens when timelines are missed</li>
        <li>Your rights at CSE meetings — including the right to bring advocates and record proceedings</li>
        <li>Discipline protections under the IDEA, including Manifestation Determination Reviews</li>
        <li>How to request an Independent Educational Evaluation (IEE) at district expense</li>
        <li>Local attorneys, advocates, and evaluators who serve that community</li>
      </ul>
    </div>

    <div class="content-section">
      <h2>What We Are Not</h2>
      <p>We are not a government agency, law firm, or advocacy organization. Nothing on this site constitutes legal advice. We are an independent informational resource run by a New York parent.</p>
    </div>

    <div class="content-section">
      <h2>Our Commitment to Parents</h2>
      <p>We do not take money from school districts. We do not accept advertising from any party with financial interest in minimizing special education services. The only paid placements on this site are from private practitioners — attorneys, advocates, and evaluators — who serve families, not districts.</p>
      <p>Every resource we link to has been reviewed for relevance and accuracy. We update pages when laws or district policies change.</p>
    </div>

    <div class="insight-box" style="margin-top:40px;">
      <div class="insight-icon"><i class="fas fa-envelope"></i></div>
      <div class="insight-text">
        <h4>Questions or corrections?</h4>
        <p>If you find an error or have information that would help other parents, <a href="/contact">contact us here</a>.</p>
      </div>
    </div>

  </div>
</main>
{std_footer()}
</body>
</html>"""
        if dry_run:
            log.info("  [DRY RUN] Would create: about/mission.html")
        else:
            mission_path.write_text(mission_html, encoding="utf-8")
            log.info(f"  ✓ Created: {mission_path}")

    # --- methodology.html ---
    methodology_path = about_dir / "methodology.html"
    if methodology_path.exists():
        log.info("  SKIP methodology.html — already exists")
    else:
        methodology_html = f"""<!DOCTYPE html>
<html lang="en">
{site_head(
    "Our Methodology | NY Special Ed",
    "How NY Special Ed selects districts, researches content, vets provider listings, and maintains accuracy across New York State special education resources.",
    f"{SITE_BASE_URL}/about/methodology"
)}
<body>
<!-- ny-methodology-v1 -->
{std_header()}
<section class="page-hero-dark">
  <div class="container">
    <h1>Our Methodology</h1>
    <p class="hero-sub">How we research, build, and maintain this resource.</p>
  </div>
</section>
<main>
  <div class="container" style="max-width:760px; padding:48px 24px;">

    <div class="content-section">
      <h2>How We Select Districts</h2>
      <p>We prioritize school districts in New York State based on enrollment size, demonstrated parent demand, and known concentrations of special education dispute activity. For New York City, we maintain pages for each of the 32 community school districts plus District 75. Statewide, we cover the Big 5 cities and the largest suburban districts across Long Island, Westchester, and upstate regions.</p>
    </div>

    <div class="content-section">
      <h2>How We Research Content</h2>
      <p>Content on each district page is based on:</p>
      <ul>
        <li><strong>NYSED official guidance</strong> — Part 200 regulations, IDEA compliance memos, and state complaint decisions</li>
        <li><strong>NYSED State Review Office (SRO) decisions</strong> — publicly available impartial hearing decisions that reveal district-specific patterns</li>
        <li><strong>District-level data</strong> — from NYSED's data portal, including IEP rates, evaluation completion rates, and placement data</li>
        <li><strong>Community context</strong> — demographics, language access needs, and known advocacy issues in each district</li>
      </ul>
    </div>

    <div class="content-section">
      <h2>How We Vet Provider Listings</h2>
      <p>Attorneys, advocates, and evaluators can apply to be listed on district partner pages. We do not list providers without request and payment. Before approving a listing we verify:</p>
      <ul>
        <li>Bar admission or licensure status where applicable</li>
        <li>Stated service area includes the listed district</li>
        <li>No active disciplinary proceedings at time of listing</li>
      </ul>
      <p>Listing does not constitute endorsement. We recommend families independently verify credentials and speak with any provider before engaging their services.</p>
    </div>

    <div class="content-section">
      <h2>How We Stay Current</h2>
      <p>We review and update content when NYSED issues new guidance, when state law changes, or when district-specific information becomes outdated. If you see an error, <a href="/contact">let us know</a> — parents helping parents is the whole point.</p>
    </div>

    <div class="content-section">
      <h2>What We Don't Do</h2>
      <p>We do not contact school districts for comment before publishing. We do not accept payment from school districts or district consultants. We do not remove factually accurate information about district practices at district request.</p>
    </div>

  </div>
</main>
{std_footer()}
</body>
</html>"""
        if dry_run:
            log.info("  [DRY RUN] Would create: about/methodology.html")
        else:
            methodology_path.write_text(methodology_html, encoding="utf-8")
            log.info(f"  ✓ Created: {methodology_path}")


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fix 404 errors from NY Special Ed site audit")
    parser.add_argument("--dry-run",  action="store_true", help="Preview only — no files written")
    parser.add_argument("--fix",      type=str, default=None,
                        help="Comma-separated list of fix numbers to run (e.g. 1,2,5)")
    parser.add_argument("--skip",     type=str, default=None,
                        help="Comma-separated list of fix numbers to skip (e.g. 3)")
    args = parser.parse_args()

    # Determine which fixes to run
    all_fixes = {1, 2, 3, 4, 5, 6}
    if args.fix:
        run_fixes = {int(x.strip()) for x in args.fix.split(",")}
    else:
        run_fixes = all_fixes.copy()
    if args.skip:
        run_fixes -= {int(x.strip()) for x in args.skip.split(",")}

    log.info("═" * 60)
    log.info("NY Special Ed — 404 Fix Script")
    log.info(f"Site root:    {SITE_ROOT}")
    log.info(f"Districts:    {DISTRICTS_DIR}")
    log.info(f"Fixes to run: {sorted(run_fixes)}")
    if args.dry_run:
        log.info("DRY RUN MODE — no files will be written")
    log.info("═" * 60)

    fix_map = {
        1: ("Create /terms.html",                        lambda: fix_1_create_terms(args.dry_run)),
        2: ("Fix /shop links → /contact",                lambda: fix_2_remove_shop_links(args.dry_run)),
        3: ("Build missing district folders (Vertex)",   lambda: fix_3_build_missing_districts(args.dry_run)),
        4: ("Fix ../parent-advocacy-guide.html links",   lambda: fix_4_bad_guide_link(args.dry_run)),
        5: ("Lowercase mixed-case slug hrefs",           lambda: fix_5_lowercase_slugs(args.dry_run)),
        6: ("Create /about/mission + /methodology",      lambda: fix_6_create_about_pages(args.dry_run)),
    }

    for fix_num in sorted(run_fixes):
        label, fn = fix_map[fix_num]
        log.info(f"\n{'─'*60}")
        try:
            fn()
        except Exception as e:
            log.error(f"  UNHANDLED ERROR in Fix {fix_num}: {e}")
            import traceback; traceback.print_exc()

    log.info(f"\n{'═'*60}")
    log.info("Complete.")
    log.info("")
    log.info("NEXT STEPS:")
    log.info("  1. Commit changes and deploy to production")
    log.info("  2. Run Screaming Frog / Ahrefs crawl again to verify 0 404s")
    log.info("  3. Submit affected URLs to Google Search Console for re-indexing")
    log.info("  4. Check server access logs for /shop and /terms to confirm resolution")


if __name__ == "__main__":
    main()