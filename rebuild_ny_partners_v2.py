"""
rebuild_ny_partners_v2.py
--------------------------
TWO-STEP process per district:

STEP 1 — EXTRACT
  Reads existing partners.html, pulls all prose content
  (pitfalls, FAQ, regulations, advocacy tips, CSE walkthrough),
  sends to Vertex AI which restructures it into a clean
  parent-advocacy-guide.html — a new page with its own URL,
  meta description, and proper silo nav links.

STEP 2 — REBUILD
  Overwrites partners.html with the clean Texas-style
  monetization layout (hero → ad slot → insight → process
  strip → ad slots → CTA band → free resources).
  Vertex generates the short variable copy for this page.
  Silo nav on BOTH pages automatically links to
  parent-advocacy-guide.html and all other existing pages.

RESULT per district:
  partners.html              — clean monetization page
  parent-advocacy-guide.html — SEO content / long-tail ranking page

SETUP:
  pip install google-cloud-aiplatform beautifulsoup4 lxml
  gcloud auth application-default login

USAGE:
  python rebuild_ny_partners_v2.py                            # all districts
  python rebuild_ny_partners_v2.py --district albany-city-sd  # one district
  python rebuild_ny_partners_v2.py --dry-run                  # preview only
  python rebuild_ny_partners_v2.py --no-skip                  # reprocess all
  python rebuild_ny_partners_v2.py --step1-only               # extraction only
  python rebuild_ny_partners_v2.py --step2-only               # rebuild only
"""

import os, re, sys, json, time, argparse, logging
from pathlib import Path
from bs4 import BeautifulSoup, Comment
import vertexai
from vertexai.generative_models import GenerativeModel

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
DISTRICTS_DIR  = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\districts"
GCP_PROJECT_ID = "ny-build-487810"
GCP_REGION     = "us-central1"
GEMINI_MODEL   = "gemini-2.0-flash"
RATE_LIMIT_DELAY = 3        # seconds between API calls
ADVERTISE_URL    = "https://www.newyorkspecialed.net/contact"

# Markers so re-runs skip already-processed files
MARKER_GUIDE    = "<!-- ny-advocacy-guide-v1 -->"
MARKER_PARTNERS = "<!-- ny-partners-rebuilt-v1 -->"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  DISTRICT CONTEXT
# ──────────────────────────────────────────────
DISTRICT_CONTEXT = {
    "albany-city-sd":        {"type":"urban",    "city":"Albany",          "county":"Albany",     "notes":"state capital, 72% high needs, large ELL population, bilingual evals critical"},
    "buffalo-city-sd":       {"type":"urban",    "city":"Buffalo",         "county":"Erie",       "notes":"large urban, high poverty, significant ELL population"},
    "rochester-city-sd":     {"type":"urban",    "city":"Rochester",       "county":"Monroe",     "notes":"large urban, high needs, high IEP rate, strong parent advocacy orgs nearby"},
    "syracuse-city-sd":      {"type":"urban",    "city":"Syracuse",        "county":"Onondaga",   "notes":"large urban, high poverty, evaluation delay concerns"},
    "yonkers-city-sd":       {"type":"urban",    "city":"Yonkers",         "county":"Westchester","notes":"urban, large ELL population, proximity to NYC advocacy resources"},
    "nyc-district-01-lower-east-side": {"type":"urban",    "city":"Manhattan",  "county":"New York",  "notes":"high density, diverse, many bilingual families"},
    "nyc-district-02-upper-east-side": {"type":"suburban", "city":"Manhattan",  "county":"New York",  "notes":"affluent, high private eval rate, LRE disputes common"},
    "nyc-district-03-upper-west-side": {"type":"suburban", "city":"Manhattan",  "county":"New York",  "notes":"affluent, active parent community, 2e overlap"},
    "nyc-district-04-east-harlem":     {"type":"urban",    "city":"Manhattan",  "county":"New York",  "notes":"high needs, ELL population, bilingual IEP rights important"},
    "nyc-district-05-central-harlem":  {"type":"urban",    "city":"Manhattan",  "county":"New York",  "notes":"high needs, evaluation access concerns"},
    "nyc-district-06-washington-heights":{"type":"urban",  "city":"Manhattan",  "county":"New York",  "notes":"large Dominican community, bilingual evals critical"},
    "nyc-district-13-brooklyn-heights":{"type":"suburban", "city":"Brooklyn",   "county":"Kings",     "notes":"affluent, high private eval rate"},
    "nyc-district-15-park-slope":      {"type":"suburban", "city":"Brooklyn",   "county":"Kings",     "notes":"mix affluent/high needs, active advocacy community"},
    "nyc-district-20-bay-ridge":       {"type":"suburban", "city":"Brooklyn",   "county":"Kings",     "notes":"middle-class diverse, Arab-American community"},
    "nyc-district-22-flatbush":        {"type":"urban",    "city":"Brooklyn",   "county":"Kings",     "notes":"diverse Caribbean community, evaluation delays reported"},
    "nyc-district-24-corona":          {"type":"urban",    "city":"Queens",     "county":"Queens",    "notes":"large immigrant community, high ELL, bilingual sped critical"},
    "nyc-district-26-bayside":         {"type":"suburban", "city":"Queens",     "county":"Queens",    "notes":"middle-class, Asian-American community, private eval culture"},
    "nyc-district-28-forest-hills":    {"type":"suburban", "city":"Queens",     "county":"Queens",    "notes":"affluent, high private eval rate, active parent community"},
    "nyc-district-30-astoria":         {"type":"urban",    "city":"Queens",     "county":"Queens",    "notes":"diverse, growing immigrant population"},
    "nyc-district-31-staten-island":   {"type":"suburban", "city":"Staten Island","county":"Richmond","notes":"suburban, middle-class, parents often seek private evals"},
    "nyc-district-75":                 {"type":"urban",    "city":"New York City","county":"Citywide", "notes":"citywide district for students with significant disabilities"},
    "default":                         {"type":"suburban", "city":"New York",   "county":"New York",  "notes":"New York State school district"},
}

def get_ctx(slug):
    return DISTRICT_CONTEXT.get(slug, DISTRICT_CONTEXT["default"])

def slug_to_name(slug):
    UPPERS = {"sd","csd","ufsd","nyc"}
    return " ".join(
        w.upper() if w.lower() in UPPERS else w.capitalize()
        for w in slug.replace("-"," ").split()
    )

def get_silo_pages(folder, include_guide=False):
    """Return dict of silo pages that exist in this folder."""
    candidates = {
        "index":    "index.html",
        "cse":      "cse-meeting-guide.html",
        "evaluation":"evaluation-process.html",
        "discipline":"discipline-rights.html",
        "contacts": "leadership-directory.html",
        "updates":  "special-ed-updates.html",
        "partners": "partners.html",
    }
    if include_guide:
        candidates["guide"] = "parent-advocacy-guide.html"

    return {k: v for k, v in candidates.items()
            if k == "guide" or (folder / v).exists()}

def build_silo_nav(district_name, silo_pages, active_page):
    """Build silo nav HTML. active_page = key from silo_pages dict."""
    labels = {
        "index":      "District Home",
        "cse":        "CSE Guide",
        "evaluation": "Evaluations",
        "discipline": "Discipline Rights",
        "contacts":   "Contacts",
        "updates":    "Updates",
        "partners":   "Providers &amp; Support",
        "guide":      "Advocacy Guide",
    }
    links = []
    for key, filename in silo_pages.items():
        label = labels.get(key, key.capitalize())
        cls = ' class="active"' if key == active_page else ''
        links.append(f'<a href="{filename}"{cls}>{label}</a>')
    nav_links = "\n      ".join(links)
    return f"""<nav class="silo-nav" aria-label="District pages">
      <strong>{district_name} Resources:</strong>
      {nav_links}
    </nav>"""


# ══════════════════════════════════════════════
#  STEP 1 — EXTRACT PROSE → parent-advocacy-guide.html
# ══════════════════════════════════════════════

def extract_prose_content(html: str) -> str:
    """
    Pull all meaningful prose text blocks from the existing partners.html.
    Returns a plain-text / lightly-tagged string Vertex can work with.
    Strips nav, header, footer, ad slots, contact tables, scripts.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove elements we never want
    for tag in soup.find_all([
        "header","footer","nav","script","style","noscript",
    ]):
        tag.decompose()

    # Remove ad slot blocks by class
    ad_classes = [
        "featured-ad-zone","featured-partner-hero","ad-slot-card",
        "ad-slot-available","category-featured","ribbon","ribbon-wrapper",
        "ad-badge-premium","btn-claim","hero-cta","partner-cta-band",
        "contact-table-section","contact-panel","contact-grid",
        "district-quick-stats","hero-stats","silo-nav","trust-anchor",
        "directory-filters","process-strip","process-grid","insight-box",
        "free-resources-section","resource-tier","free-banner",
    ]
    for cls in ad_classes:
        for el in soup.find_all(class_=cls):
            el.decompose()

    # Get remaining text with basic structure preserved
    text_blocks = []
    for tag in soup.find_all(["h2","h3","h4","h5","p","li","dt","dd","ol","ul"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 40:  # skip tiny fragments
            if tag.name in ("h2","h3","h4","h5"):
                text_blocks.append(f"\n## {text}\n")
            else:
                text_blocks.append(text)

    result = "\n".join(text_blocks)
    # Collapse excessive whitespace
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def build_guide_prompt(district_name: str, slug: str, prose: str) -> str:
    ctx = get_ctx(slug)
    return f"""You are restructuring extracted content into a clean HTML page for a 
New York special education parent resource website.

District: {district_name}
City: {ctx['city']} | County: {ctx['county']} | Type: {ctx['type']}
Context: {ctx['notes']}

The EXTRACTED CONTENT below came from a dense existing page. Your job is to 
restructure it into a well-organized parent advocacy guide.

Return ONLY a raw JSON object. No markdown. No explanation. Exactly these keys:

{{
  "meta_description": "...",
  "meta_title": "...",
  "intro_p": "...",
  "sections": [
    {{
      "h2": "...",
      "content_html": "..."
    }}
  ],
  "faq": [
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}}
  ],
  "cta_p": "..."
}}

RULES:

meta_title (60 chars max):
- Format: "CSE Advocacy Guide for {district_name} Parents | NY Special Ed"

meta_description (140-160 chars):
- Mention {district_name}, CSE meetings, parent rights, and IEP advocacy
- Do not start with "Find"

intro_p (2-3 sentences):
- Warm opening paragraph acknowledging the parent's challenge
- Mention {district_name} specifically
- Reference NY State CSE process

sections (3-5 sections extracted and restructured from the content):
- h2: clear descriptive heading
- content_html: clean HTML using only <p>, <ul>, <li>, <strong>, <ol> tags
- Reorganize and improve clarity — do not just copy paste
- Remove any advertiser placeholder text
- Update any Texas/ARD references to NY/CSE equivalents
- Each section should be genuinely useful to a parent

faq (3-5 questions extracted or derived from the content):
- q: a real question a parent would Google
- a: 2-4 sentence plain text answer
- Must include {district_name} naturally in at least 2 answers
- Focus on practical actionable information

cta_p (1-2 sentences):
- Transition sentence linking to partners page for local provider help
- Example: "Ready to find a local advocate or evaluator in {district_name}? 
  Browse our vetted provider directory."

EXTRACTED CONTENT TO RESTRUCTURE:
{prose[:4000]}
"""


def build_guide_html(district_name: str, slug: str,
                     silo_pages: dict, data: dict) -> str:
    """Render the full parent-advocacy-guide.html page."""

    silo_nav = build_silo_nav(district_name, silo_pages, "guide")

    # Sections
    sections_html = ""
    for sec in data.get("sections", []):
        sections_html += f"""
    <div class="content-section">
      <h2>{sec['h2']}</h2>
      {sec['content_html']}
    </div>"""

    # FAQ
    faq_html = ""
    for item in data.get("faq", []):
        faq_html += f"""
      <div class="faq-item">
        <h3>{item['q']}</h3>
        <p>{item['a']}</p>
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{data['meta_title']}</title>
  <meta name="description" content="{data['meta_description']}"/>
  <link rel="canonical" href="https://www.newyorkspecialed.net/districts/{slug}/parent-advocacy-guide.html"/>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"/>
  <link href="/styles/global.css" rel="stylesheet"/>
  <link href="/styles/styles-nav-footer.css" rel="stylesheet"/>
</head>
<body>
{MARKER_GUIDE}

<!-- ═══ HEADER ═══ -->
<header class="site-header">
  <!-- standard NY header here -->
</header>

<!-- ═══ HERO ═══ -->
<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{district_name}</span>
    <h1>Parent Advocacy Guide<br/>for {district_name}</h1>
    <p class="hero-sub">Practical strategies for navigating the CSE process, understanding your rights, and advocating effectively for your child in {district_name}.</p>
  </div>
</section>

<main>
  <div class="container">

    {silo_nav}

    <div class="trust-anchor">
      <strong>Hi, I'm a New York parent of a child with an IEP.</strong> When I watched the system fail my child, I realized how broken the CSE process is. I built this resource to help parents like you get the services your child deserves. You are not alone.
    </div>

    <hr class="divider" style="margin:8px 0 40px;"/>

    <!-- ═══ INTRO ═══ -->
    <div class="content-intro">
      <p>{data['intro_p']}</p>
    </div>

    <!-- ═══ MAIN CONTENT SECTIONS ═══ -->
    {sections_html}

    <!-- ═══ FAQ ═══ -->
    <div class="faq-section" style="margin-top:48px;">
      <div class="section-title-row">
        <h2>Frequently Asked Questions</h2>
        <span>{district_name} parents ask</span>
      </div>
      {faq_html}
    </div>

    <!-- ═══ CTA TO PARTNERS PAGE ═══ -->
    <div class="insight-box" style="margin-top:48px;">
      <div class="insight-icon"><i class="fas fa-hands-helping"></i></div>
      <div class="insight-text">
        <h4>Need a local advocate or evaluator?</h4>
        <p>{data['cta_p']} <a href="partners.html">Browse local providers in {district_name} &rarr;</a></p>
      </div>
    </div>

  </div>
</main>

<!-- ═══ FOOTER ═══ -->
<footer class="site-footer">
  <!-- standard NY footer here -->
</footer>

</body>
</html>"""


# ══════════════════════════════════════════════
#  STEP 2 — REBUILD partners.html (clean layout)
# ══════════════════════════════════════════════

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
          </a>
          <a class="free-card" href="https://www.includenyc.org" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-hands-helping"></i></div>
            <div class="free-card-text"><strong>INCLUDEnyc</strong>
              <span>Free helpline and resources for NYC families of children with disabilities.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>"""

NATIONAL_RESOURCES = """
          <a class="free-card" href="https://www.wrightslaw.com" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-balance-scale"></i></div>
            <div class="free-card-text"><strong>Wrightslaw</strong>
              <span>Free guides on special education law, IEPs, and parent rights under IDEA.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>
          <a class="free-card" href="https://www.parentcenterhub.org/find-your-center/" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-users"></i></div>
            <div class="free-card-text"><strong>Parent Training &amp; Information Centers</strong>
              <span>Federally funded free training for families of children with disabilities.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>
          <a class="free-card" href="https://www.understood.org" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-brain"></i></div>
            <div class="free-card-text"><strong>Understood.org</strong>
              <span>Free expert guidance for parents of children with learning differences.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>"""


def build_partners_prompt(district_name: str, slug: str) -> str:
    ctx = get_ctx(slug)
    return f"""You are writing short localized copy for a New York special education 
parent resource website. District: {district_name}, City: {ctx['city']}, 
Type: {ctx['type']}, Context: {ctx['notes']}

Return ONLY raw JSON. No markdown. No explanation.

{{
  "meta_description": "...",
  "insight_h4": "...",
  "insight_p": "...",
  "process_items": [
    {{"h4": "...", "p": "..."}},
    {{"h4": "...", "p": "..."}},
    {{"h4": "...", "p": "..."}}
  ],
  "local_resources": [
    {{"icon": "fas fa-...", "name": "...", "url": "https://...", "desc": "..."}},
    {{"icon": "fas fa-...", "name": "...", "url": "https://...", "desc": "..."}}
  ]
}}

meta_description: 140-160 chars, mention {district_name}, CSE meetings, 
local advocates. Do not start with "Find".

insight_h4: 6-10 words, mention {district_name}
insight_p: 2-3 sentences about free services available. Urban = bilingual 
evals/autism support. Suburban = inclusion/ESY/2e. Plain text only.

process_items: 3 distinct items.
- h4: 3-5 words
- p: max 15 words
- Urban: evaluation delays, bilingual CSE rights, MDR/discipline issues
- Suburban: LRE placement fights, IEE rights, transition planning

local_resources: exactly 2 REAL organizations serving {ctx['city']} or 
{ctx['county']} County. Must have real working URLs. Use county Arc chapters, 
SETRC offices, legal aid societies, university clinics, hospital eval centers.
Do NOT include: DRNY, Advocates for Children, INCLUDEnyc, NYSED (already listed).
"""


def build_partners_html(district_name: str, slug: str,
                        silo_pages: dict, data: dict) -> str:
    """Render the clean partners.html monetization page."""

    silo_nav = build_silo_nav(district_name, silo_pages, "partners")

    proc_html = ""
    for i, item in enumerate(data["process_items"], 1):
        proc_html += f"""      <div class="process-item">
        <div class="process-num">{i}</div>
        <div class="process-body">
          <h4>{item['h4']}</h4>
          <p>{item['p']}</p>
        </div>
      </div>\n"""

    local_html = ""
    for r in data.get("local_resources", []):
        local_html += f"""          <a class="free-card" href="{r['url']}" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="{r['icon']}"></i></div>
            <div class="free-card-text"><strong>{r['name']}</strong>
              <span>{r['desc']}</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>\n"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Special Education Providers &amp; Support in {district_name} | NY Special Ed</title>
  <meta name="description" content="{data['meta_description']}"/>
  <link rel="canonical" href="https://www.newyorkspecialed.net/districts/{slug}/partners.html"/>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"/>
  <link href="/styles/global.css" rel="stylesheet"/>
  <link href="/styles/styles-nav-footer.css" rel="stylesheet"/>
  <link href="/styles/partners.css" rel="stylesheet"/>
</head>
<body>
{MARKER_PARTNERS}

<header class="site-header">
  <!-- standard NY header here -->
</header>

<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{district_name}</span>
    <h1>Special Education Providers<br/>in {district_name}</h1>
    <p class="hero-sub">Connect with local advocates, attorneys, and evaluators who know New York special education law — and the CSE process in {district_name} specifically.</p>
  </div>
</section>

<main>
  <div class="container">

    {silo_nav}

    <div class="trust-anchor">
      <strong>Hi, I'm a New York parent of a child with an IEP.</strong> When I watched the system fail my child, I realized how broken the CSE process is. I built this resource to help parents like you get the services your child deserves. You are not alone.
    </div>

    <hr class="divider" style="margin:8px 0 40px;"/>

    <!-- FEATURED AD SLOT -->
    <div class="featured-ad-zone">
      <span class="ad-badge-premium">District Exclusive</span>
      <div class="ad-logo-box">
        <i class="fas fa-building"></i>
        <span>Your Logo</span>
      </div>
      <div class="ad-content">
        <span class="label label-gold">Featured Partner</span>
        <h3>Position your practice as the trusted authority in {district_name}</h3>
        <p>Capture high-intent parents seeking independent evaluations, neuropsychological testing, or CSE advocacy — right when they need it most. One exclusive listing per district.</p>
        <div class="ad-tags">
          <span class="ad-tag">IEE Evaluations</span>
          <span class="ad-tag">CSE Advocacy</span>
          <span class="ad-tag">Neuropsych Testing</span>
          <span class="ad-tag">Legal Support</span>
        </div>
      </div>
      <a class="btn-claim" href="{ADVERTISE_URL}">
        Reserve This Spot <i class="fas fa-arrow-right" style="font-size:.75rem;"></i>
      </a>
    </div>

    <!-- INSIGHT BOX -->
    <div class="insight-box">
      <div class="insight-icon"><i class="fas fa-lightbulb"></i></div>
      <div class="insight-text">
        <h4>{data['insight_h4']}</h4>
        <p>{data['insight_p']}</p>
      </div>
    </div>

    <!-- PROCESS STRIP -->
    <div class="section-title-row">
      <h2>Navigating Special Ed in {district_name}</h2>
      <span>Key rights to know &mdash; <a href="parent-advocacy-guide.html">read the full guide &rarr;</a></span>
    </div>
    <div class="process-strip">
{proc_html}    </div>

    <!-- AD SLOTS -->
    <div class="section-title-row mt-56">
      <h2>Advocates &amp; CSE Support</h2>
      <span>Local area providers</span>
    </div>
    <div class="ad-slot-card">
      <div class="ad-slot-logo"><i class="fas fa-user-tie fa-lg"></i></div>
      <div class="ad-slot-content">
        <h4>Your Advocacy Firm</h4>
        <p>Be the first advocate parents call when they hit a wall at the CSE table. Exclusive to this category in {district_name}.</p>
      </div>
      <a href="{ADVERTISE_URL}" class="ad-slot-cta">Claim this listing <i class="fas fa-chevron-right" style="font-size:.65rem;"></i></a>
    </div>

    <div class="section-title-row mt-48">
      <h2>Special Education Attorneys</h2>
      <span>Impartial hearings &amp; NYSED complaints</span>
    </div>
    <div class="ad-slot-card">
      <div class="ad-slot-logo"><i class="fas fa-scale-balanced fa-lg"></i></div>
      <div class="ad-slot-content">
        <h4>Your Law Firm</h4>
        <p>Position your firm as the go-to legal resource for families in {district_name} navigating due process or NYSED complaints.</p>
      </div>
      <a href="{ADVERTISE_URL}" class="ad-slot-cta">Claim this listing <i class="fas fa-chevron-right" style="font-size:.65rem;"></i></a>
    </div>

    <div class="section-title-row mt-48">
      <h2>Independent Evaluators</h2>
      <span>IEE, neuropsychological &amp; specialty</span>
    </div>
    <div class="ad-slot-card">
      <div class="ad-slot-logo"><i class="fas fa-brain fa-lg"></i></div>
      <div class="ad-slot-content">
        <h4>Your Evaluation Practice</h4>
        <p>Reach parents in {district_name} seeking an independent second opinion after the district's evaluation.</p>
      </div>
      <a href="{ADVERTISE_URL}" class="ad-slot-cta">Claim this listing <i class="fas fa-chevron-right" style="font-size:.65rem;"></i></a>
    </div>

    <div class="section-title-row mt-48">
      <h2>Therapists &amp; Related Services</h2>
      <span>Speech, OT, PT &amp; counseling</span>
    </div>
    <div class="ad-slot-card">
      <div class="ad-slot-logo"><i class="fas fa-heart-pulse fa-lg"></i></div>
      <div class="ad-slot-content">
        <h4>Your Therapy Practice</h4>
        <p>Connect with families whose children need private therapy to supplement their IEP services in {district_name}.</p>
      </div>
      <a href="{ADVERTISE_URL}" class="ad-slot-cta">Claim this listing <i class="fas fa-chevron-right" style="font-size:.65rem;"></i></a>
    </div>

  </div>

  <!-- PARTNER CTA BAND -->
  <div class="container">
    <div class="partner-cta-band">
      <div class="partner-cta-copy">
        <span class="label label-muted">For Practices &amp; Firms</span>
        <h2>Why Partner With NY Special Ed?</h2>
        <p>We are the only independent resource hub for New York special education parents. Our {district_name} pages capture high-intent traffic from families actively seeking evaluations and legal support — often within hours of a CSE meeting.</p>
      </div>
      <a href="{ADVERTISE_URL}" class="btn-partner">
        Become a Partner <i class="fas fa-arrow-right" style="font-size:.75rem;"></i>
      </a>
    </div>
  </div>

  <!-- FREE RESOURCES -->
  <div class="container">
    <section class="free-resources-section">
      <div class="free-resources-intro">
        <span class="label label-green">No cost to families</span>
        <h2>Free &amp; Non-Profit Resources</h2>
      </div>
      <div class="resource-tier tier-national">
        <div class="tier-header"><i class="fas fa-flag-usa"></i> National Free Resources</div>
        <div class="tier-body">{NATIONAL_RESOURCES}</div>
      </div>
      <div class="resource-tier tier-state">
        <div class="tier-header"><i class="fas fa-star"></i> New York State Resources</div>
        <div class="tier-body">{NY_STATE_RESOURCES}</div>
      </div>
      <div class="resource-tier tier-local">
        <div class="tier-header"><i class="fas fa-map-marker-alt"></i> Local Resources &mdash; {district_name} Area</div>
        <div class="tier-body">
{local_html}        </div>
      </div>
    </section>
  </div>

</main>

<footer class="site-footer">
  <!-- standard NY footer here -->
</footer>

</body>
</html>"""


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def process_district(folder: Path, model, args):
    slug = folder.name
    district_name = slug_to_name(slug)
    partners_file = folder / "partners.html"
    guide_file    = folder / "parent-advocacy-guide.html"

    log.info(f"── {district_name} ──────────────────────────")

    # ── STEP 1: Extract → parent-advocacy-guide.html ──────────
    if not args.step2_only:
        skip_guide = (not args.no_skip and guide_file.exists() and
                      MARKER_GUIDE in guide_file.read_text(encoding="utf-8", errors="replace"))
        if skip_guide:
            log.info("  Step 1 SKIP — advocacy guide already exists")
        elif not partners_file.exists():
            log.warning("  Step 1 SKIP — no partners.html to extract from")
        else:
            existing_html = partners_file.read_text(encoding="utf-8", errors="replace")

            # Don't try to extract if already rebuilt (no prose left)
            if MARKER_PARTNERS in existing_html:
                log.info("  Step 1 SKIP — partners.html already rebuilt, no prose to extract")
            else:
                prose = extract_prose_content(existing_html)
                if len(prose) < 200:
                    log.warning(f"  Step 1 SKIP — not enough prose content extracted ({len(prose)} chars)")
                else:
                    log.info(f"  Step 1: Extracted {len(prose)} chars of prose")
                    prompt = build_guide_prompt(district_name, slug, prose)
                    try:
                        response = model.generate_content(prompt)
                        raw = response.text.strip()
                        raw = re.sub(r"^```json\s*","",raw)
                        raw = re.sub(r"^```\s*","",raw)
                        raw = re.sub(r"\s*```$","",raw)
                        guide_data = json.loads(raw)
                    except Exception as e:
                        log.error(f"  Step 1 ERROR — {e}")
                        guide_data = None

                    if guide_data:
                        # Silo pages for guide include guide itself
                        silo = get_silo_pages(folder, include_guide=True)
                        guide_html = build_guide_html(district_name, slug, silo, guide_data)
                        if args.dry_run:
                            log.info(f"  [DRY RUN] Would write: {guide_file.name}")
                            log.info(f"    title  : {guide_data.get('meta_title','')[:60]}")
                            log.info(f"    sections: {[s['h2'] for s in guide_data.get('sections',[])]}")
                            log.info(f"    faq    : {len(guide_data.get('faq',[]))} items")
                        else:
                            guide_file.write_text(guide_html, encoding="utf-8")
                            log.info(f"  ✓ Wrote: {guide_file.name}")

        time.sleep(RATE_LIMIT_DELAY)

    # ── STEP 2: Rebuild partners.html ─────────────────────────
    if not args.step1_only:
        skip_partners = (not args.no_skip and partners_file.exists() and
                         MARKER_PARTNERS in partners_file.read_text(encoding="utf-8", errors="replace"))
        if skip_partners:
            log.info("  Step 2 SKIP — partners.html already rebuilt")
        else:
            prompt2 = build_partners_prompt(district_name, slug)
            try:
                response2 = model.generate_content(prompt2)
                raw2 = response2.text.strip()
                raw2 = re.sub(r"^```json\s*","",raw2)
                raw2 = re.sub(r"^```\s*","",raw2)
                raw2 = re.sub(r"\s*```$","",raw2)
                partners_data = json.loads(raw2)
            except Exception as e:
                log.error(f"  Step 2 ERROR — {e}")
                return

            # Silo pages now include the guide page we just created
            silo2 = get_silo_pages(folder, include_guide=True)
            partners_html = build_partners_html(district_name, slug, silo2, partners_data)

            if args.dry_run:
                log.info(f"  [DRY RUN] Would rebuild: {partners_file.name}")
                log.info(f"    meta   : {partners_data.get('meta_description','')[:80]}")
                log.info(f"    cards  : {[c['h4'] for c in partners_data.get('process_items',[])]}")
                log.info(f"    local  : {[r['name'] for r in partners_data.get('local_resources',[])]}")
            else:
                partners_file.write_text(partners_html, encoding="utf-8")
                log.info(f"  ✓ Rebuilt: {partners_file.name}")

        time.sleep(RATE_LIMIT_DELAY)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",    action="store_true", help="Preview only, no file writes")
    parser.add_argument("--district",   type=str,  default=None, help="Process single district slug")
    parser.add_argument("--no-skip",    action="store_true", help="Reprocess already-done files")
    parser.add_argument("--step1-only", action="store_true", help="Only run extraction step")
    parser.add_argument("--step2-only", action="store_true", help="Only run partners rebuild step")
    args = parser.parse_args()

    log.info(f"Vertex AI init — project={GCP_PROJECT_ID}  model={GEMINI_MODEL}")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    model = GenerativeModel(GEMINI_MODEL)

    districts_path = Path(DISTRICTS_DIR)
    if not districts_path.exists():
        log.error(f"Not found: {DISTRICTS_DIR}")
        sys.exit(1)

    SKIP_FOLDERS = {
    "about", "contact", "resources", "blog", "images",
    "styles", "css", "js", "assets", "guides", "shop",
    "privacy-policy", "terms", "sitemap", "advertise"
}

    folders = sorted([
    f for f in districts_path.iterdir()
    if f.is_dir()
    and f.name not in SKIP_FOLDERS
    and (args.district is None or f.name == args.district)
])
    log.info(f"Districts to process: {len(folders)}")
    if args.dry_run:
        log.info("DRY RUN MODE — no files will be written")

    for folder in folders:
        try:
            process_district(folder, model, args)
        except Exception as e:
            log.error(f"  UNHANDLED ERROR {folder.name}: {e}")

    log.info("═" * 55)
    log.info("Complete.")


if __name__ == "__main__":
    main()