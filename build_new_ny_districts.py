"""
build_new_ny_districts.py
──────────────────────────────────────────────────────────
Builds ALL pages for brand-new NY special education districts
from scratch using Vertex AI (Gemini Flash).

Pages generated per district:
  index.html                  district hub / home page
  cse-meeting-guide.html      CSE meeting parent guide
  evaluation-process.html     evaluation & IEE rights
  discipline-rights.html      discipline / impartial hearing rights
  leadership-directory.html   CSE contact directory stub
  special-ed-updates.html     district news / updates stub
  partners.html               monetization / provider page
  parent-advocacy-guide.html  long-form SEO guide

Also updates the main districts listing index page to
add the new districts as hub cards.

SETUP:
  pip install google-cloud-aiplatform beautifulsoup4 lxml
  gcloud auth application-default login

USAGE:
  python build_new_ny_districts.py                          # build all new districts
  python build_new_ny_districts.py --district sachem-csd   # single district
  python build_new_ny_districts.py --dry-run               # preview only
  python build_new_ny_districts.py --no-skip               # force rebuild
  python build_new_ny_districts.py --skip-index-update     # skip main index edit
"""

import os, re, sys, json, time, argparse, logging
from pathlib import Path
from bs4 import BeautifulSoup
import vertexai
from vertexai.generative_models import GenerativeModel

# ──────────────────────────────────────────────
#  CONFIG  — update GCP_PROJECT_ID before running
# ──────────────────────────────────────────────
DISTRICTS_DIR  = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\districts"
GCP_PROJECT_ID = "ny-build-487810"
GCP_REGION     = "us-central1"
GEMINI_MODEL   = "gemini-2.0-flash"
RATE_LIMIT_DELAY = 3          # seconds between API calls
ADVERTISE_URL    = "https://www.newyorkspecialed.net/contact"
SITE_BASE_URL    = "https://www.newyorkspecialed.net"

# Build markers — skip pages that already have these
MARKER_INDEX    = "<!-- ny-index-v1 -->"
MARKER_CSE      = "<!-- ny-cse-guide-v1 -->"
MARKER_EVAL     = "<!-- ny-eval-v1 -->"
MARKER_DISC     = "<!-- ny-discipline-v1 -->"
MARKER_DIR      = "<!-- ny-directory-v1 -->"
MARKER_UPDATES  = "<!-- ny-updates-v1 -->"
MARKER_PARTNERS = "<!-- ny-partners-rebuilt-v1 -->"
MARKER_GUIDE    = "<!-- ny-advocacy-guide-v1 -->"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  NEW DISTRICTS TO BUILD
# ──────────────────────────────────────────────
NEW_DISTRICTS = {
    "sachem-csd": {
        "name":   "Sachem CSD",
        "type":   "suburban",
        "city":   "Lake Ronkonkoma",
        "county": "Suffolk",
        "region": "Long Island",
        "enrollment": "~11,700",
        "notes":  "Large suburban Long Island district, 40% minority enrollment, 20% economically disadvantaged. District has had documented special ed budget pressures — BOE voted to cut activities to reallocate funds to special education. Parents active in IEP disputes, especially around LRE placement and transition planning. Private eval culture strong in surrounding area.",
    },
    "greece-csd": {
        "name":   "Greece CSD",
        "type":   "suburban",
        "city":   "Greece",
        "county": "Monroe",
        "region": "Upstate",
        "enrollment": "~10,200",
        "notes":  "Suburban Rochester district, town of Greece in Monroe County. Mix of working-class and middle-class families. Sits adjacent to Rochester City SD. Parents often compare services to neighboring districts. Evaluation delays and LRE placement concerns common. Rochester-area advocacy orgs serve this district.",
    },
    "east-ramapo-csd": {
        "name":   "East Ramapo CSD",
        "type":   "urban",
        "city":   "Spring Valley",
        "county": "Rockland",
        "region": "Hudson Valley",
        "enrollment": "~8,500",
        "notes":  "One of the most controversial districts in NY State. Has been under state oversight for years due to board majority diverting public school resources to private yeshivas. Large Black and Latino public school population, large Orthodox Jewish private school community. Chronic underfunding of public special education. Very high parent-attorney activity. State monitor appointed. Bilingual sped services underfunded. This district generates disproportionate legal activity relative to its size.",
    },
    "patchogue-medford-ufsd": {
        "name":   "Patchogue-Medford UFSD",
        "type":   "suburban",
        "city":   "Patchogue",
        "county": "Suffolk",
        "region": "Long Island",
        "enrollment": "~8,900",
        "notes":  "Mid-size Suffolk County district on Long Island south shore. Diverse population, significant Latino community. Evaluation timeline compliance has been an issue. Parents increasingly seeking IEEs after district evaluations. Proximity to Bay Shore UFSD and Brentwood UFSD means attorneys often serve multiple nearby districts.",
    },
}

# ──────────────────────────────────────────────
#  SHARED STATIC RESOURCES
# ──────────────────────────────────────────────
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
              <span>Free legal advocacy for New Yorkers with disabilities, including IEP disputes.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>
          <a class="free-card" href="https://www.advocatesforchildren.org" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-child"></i></div>
            <div class="free-card-text"><strong>Advocates for Children of New York</strong>
              <span>Free legal representation for NYC-area students in special education disputes.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>
          <a class="free-card" href="https://www.parentcenterhub.org/find-your-center/" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-users"></i></div>
            <div class="free-card-text"><strong>NY Parent Training &amp; Information Center</strong>
              <span>Free federally funded training and support for NY families of children with disabilities.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>"""

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
          </a>
          <a class="free-card" href="https://www.parentcenterhub.org/find-your-center/" target="_blank" rel="noopener">
            <div class="free-card-icon"><i class="fas fa-users"></i></div>
            <div class="free-card-text"><strong>Parent Training &amp; Information Centers</strong>
              <span>Federally funded free training for families of children with disabilities.</span></div>
            <i class="fas fa-external-link-alt free-card-arrow"></i>
          </a>"""


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────
def build_silo_nav(district_name: str, slug: str, active: str, has_guide: bool = True) -> str:
    pages = [
        ("index",     "index.html",                  "District Home"),
        ("cse",       "cse-meeting-guide.html",       "CSE Guide"),
        ("eval",      "evaluation-process.html",      "Evaluations"),
        ("disc",      "discipline-rights.html",       "Discipline Rights"),
        ("contacts",  "leadership-directory.html",    "Contacts"),
        ("updates",   "special-ed-updates.html",      "Updates"),
        ("partners",  "partners.html",                "Providers &amp; Support"),
    ]
    if has_guide:
        pages.append(("guide", "parent-advocacy-guide.html", "Advocacy Guide"))

    links = []
    for key, href, label in pages:
        cls = ' class="active"' if key == active else ""
        links.append(f'<a href="{href}"{cls}>{label}</a>')

    return f"""<nav class="silo-nav" aria-label="District pages">
      <strong>{district_name} Resources:</strong>
      {"      ".join(links)}
    </nav>"""


def call_vertex(model, prompt: str, district_name: str, step: str) -> dict | None:
    """Call Vertex AI, strip markdown fences, parse JSON. Returns None on failure."""
    time.sleep(RATE_LIMIT_DELAY)
    try:
        resp = model.generate_content(prompt)
        raw  = resp.text.strip()
        raw  = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
        raw  = re.sub(r"^```\s*",     "", raw, flags=re.MULTILINE)
        raw  = re.sub(r"\s*```$",     "", raw.strip())
        return json.loads(raw)
    except Exception as e:
        log.error(f"  {step} ERROR for {district_name}: {e}")
        return None


def head(title: str, desc: str, canonical: str, extra_css: str = "") -> str:
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


def page_hero(district_name: str, label: str, h1: str, sub: str) -> str:
    return f"""<section class="page-hero-dark">
  <div class="container">
    <span class="label label-gold">{district_name}</span>
    <h1>{h1}</h1>
    <p class="hero-sub">{sub}</p>
  </div>
</section>"""


def trust_anchor() -> str:
    return """<div class="trust-anchor">
      <strong>Hi, I'm a New York parent of a child with an IEP.</strong> When I watched the system fail my child, I realized how broken the CSE process is. I built this resource to help parents like you get the services your child deserves. You are not alone.
    </div>
    <hr class="divider" style="margin:8px 0 40px;"/>"""


def std_footer() -> str:
    return """<footer class="site-footer">
  <!-- standard NY footer here -->
</footer>"""


def std_header() -> str:
    return """<header class="site-header">
  <!-- standard NY header here -->
</header>"""


# ══════════════════════════════════════════════════════════════
#  PROMPTS
# ══════════════════════════════════════════════════════════════

def prompt_index(info: dict) -> str:
    return f"""You are writing content for a New York special education parent resource website.
District: {info['name']} | County: {info['county']} | Type: {info['type']} | Enrollment: {info['enrollment']}
Context: {info['notes']}

Return ONLY a raw JSON object. No markdown. No explanation. Exactly these keys:

{{
  "meta_description": "...",
  "hero_sub": "...",
  "intro_h2": "...",
  "intro_p": "...",
  "hub_cards": [
    {{"icon": "fas fa-...", "title": "...", "desc": "...", "href": "...", "cta": "..."}},
    {{"icon": "fas fa-...", "title": "...", "desc": "...", "href": "...", "cta": "..."}},
    {{"icon": "fas fa-...", "title": "...", "desc": "...", "href": "...", "cta": "..."}},
    {{"icon": "fas fa-...", "title": "...", "desc": "...", "href": "...", "cta": "..."}}
  ],
  "quick_stats": [
    {{"label": "...", "value": "..."}},
    {{"label": "...", "value": "..."}},
    {{"label": "...", "value": "..."}}
  ],
  "local_note": "..."
}}

meta_description: 140-160 chars. Mention {info['name']}, CSE process, parent rights. Do not start with "Find".

hero_sub: 1 sentence. Acknowledge the difficulty of the CSE process in {info['name']} and promise practical help.

intro_h2: 6-10 words describing what this resource provides.

intro_p: 2-3 sentences. Warm, practical. Reference {info['county']} County and NY State CSE process. Plain text.

hub_cards: exactly 4 cards. hrefs must be exactly these (in any order):
  "cse-meeting-guide.html", "evaluation-process.html", "discipline-rights.html", "partners.html"
  icon: relevant Font Awesome 6 solid class (fa-solid prefix = fas)
  title: 3-5 words
  desc: 10-15 words describing what's on that page
  cta: 2-4 word action link text

quick_stats: 3 real or representative stats about {info['name']} special education.
  Examples: "IEP Rate", "District Enrollment", "% Students w/ Disabilities", "County CSE offices"
  Use real data if you know it, otherwise reasonable estimates for this district type.

local_note: 1-2 sentences. Mention a specific challenge or fact about special education in {info['name']} 
or {info['county']} County that a parent would find useful to know. Be specific, not generic.
"""


def prompt_cse(info: dict) -> str:
    return f"""You are writing a CSE meeting guide page for NY special education parents.
District: {info['name']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY a raw JSON object. No markdown. No explanation.

{{
  "meta_description": "...",
  "hero_sub": "...",
  "intro_p": "...",
  "sections": [
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}}
  ],
  "faq": [
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}}
  ],
  "checklist": ["...", "...", "...", "...", "..."]
}}

meta_description: 140-160 chars. Include {info['name']}, CSE meeting, parent rights. No "Find".

hero_sub: 1 sentence. What this guide helps parents do before their CSE meeting.

intro_p: 2-3 sentences. Acknowledge the stress of CSE meetings in {info['name']}, promise practical guidance.

sections: exactly 4. Use <p>, <ul>, <li>, <strong>, <ol> only in content_html.
Suggested topics (adjust for {info['type']} context):
  1. What to expect at a {info['name']} CSE meeting (agenda, participants, your role)
  2. How to prepare: documents to request 5 days before (use NY 60-school-day eval rule)
  3. Your rights AT the meeting (disagree, request adjournment, bring anyone)
  4. After the meeting: prior written notice, 10-day rule, next steps

faq: 3 questions a {info['name']} parent would Google. Include district name in ≥2 answers.
Reference NY-specific rules: 60 school days for evaluation, CPSE vs CSE, Part 200 regulations.

checklist: 5 concrete things to do before a CSE meeting. Action verbs. Short sentences.
"""


def prompt_eval(info: dict) -> str:
    return f"""You are writing an evaluation rights page for NY special education parents.
District: {info['name']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY a raw JSON object. No markdown. No explanation.

{{
  "meta_description": "...",
  "hero_sub": "...",
  "intro_p": "...",
  "sections": [
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}}
  ],
  "faq": [
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}}
  ]
}}

meta_description: 140-160 chars. Include {info['name']}, evaluation request, IEE rights. No "Find".

hero_sub: 1 sentence about requesting evaluations in {info['name']}.

intro_p: 2 sentences. Reference NY 60-school-day rule. Mention independent evaluations.

sections: 4 sections. Use <p>, <ul>, <li>, <strong>, <ol> only.
Topics:
  1. How to request a district evaluation in {info['name']} (written request, what to say)
  2. NY State evaluation timeline — the 60 school day rule and what happens if missed
  3. Your right to an Independent Educational Evaluation (IEE) at district expense
  4. Types of evaluations: neuropsych, speech, OT, PT, FBA — what to ask for

faq: 3 questions including at least one about IEEs and one about timeline. 
Include {info['name']} naturally in at least 2 answers.
All answers must reflect NY State IDEA Part 200 rules, not Texas/ARD process.
"""


def prompt_discipline(info: dict) -> str:
    return f"""You are writing a discipline rights page for NY special education parents.
District: {info['name']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY a raw JSON object. No markdown. No explanation.

{{
  "meta_description": "...",
  "hero_sub": "...",
  "intro_p": "...",
  "sections": [
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}}
  ],
  "faq": [
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}}
  ],
  "warning_signs": ["...", "...", "...", "..."]
}}

meta_description: 140-160 chars. Include {info['name']}, suspension rights, IEP discipline. No "Find".

hero_sub: 1 sentence — what parents need to know when the district disciplines their child.

intro_p: 2 sentences. IDEA discipline protections apply even in {info['name']}. Mention 10-day rule.

sections: 4 sections. Use <p>, <ul>, <li>, <strong>, <ol> only.
Topics (NY-specific, not Texas):
  1. The 10-day rule — when {info['name']} must convene a Manifestation Determination Review (MDR)
  2. What happens at an MDR — the two questions the CSE must answer
  3. If behavior IS a manifestation — the district's obligations
  4. NY impartial hearing process — how to challenge a disciplinary placement

faq: 3 questions. At least one about MDR, one about impartial hearings in NY.
Use correct NY terminology: impartial hearing officer (IHO), NYSED complaint, Part 200.

warning_signs: 4 short phrases — situations where a parent should immediately seek legal help.
"""


def prompt_directory(info: dict) -> str:
    return f"""You are writing a leadership/contacts page for a NY special education parent resource site.
District: {info['name']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY raw JSON. No markdown. No explanation.

{{
  "meta_description": "...",
  "hero_sub": "...",
  "intro_p": "...",
  "key_contacts": [
    {{"role": "...", "note": "..."}},
    {{"role": "...", "note": "..."}},
    {{"role": "...", "note": "..."}},
    {{"role": "...", "note": "..."}},
    {{"role": "...", "note": "..."}}
  ],
  "how_to_p": "...",
  "nysed_complaint_p": "..."
}}

meta_description: 140-160 chars. Include {info['name']}, CSE chairperson, special ed contacts. No "Find".
hero_sub: 1 sentence — how to reach the right people in {info['name']}'s special education system.
intro_p: 2 sentences about who parents need to contact and why.

key_contacts: 5 roles (not specific names) relevant to special ed in {info['name']}.
Examples: "CSE Chairperson", "Director of Special Education", "Assistant Superintendent for Pupil Services",
"Building Special Education Coordinator", "504 Coordinator", "School Psychologist".
note: 1 sentence explaining when/why a parent contacts this person.

how_to_p: 1-2 sentences. Practical advice on HOW to reach district staff effectively 
(e.g., FOIL requests, written vs. phone, keep records of all contact).

nysed_complaint_p: 1-2 sentences explaining that if the district is unresponsive,
parents can file a State complaint with NYSED's Office of Special Education.
"""


def prompt_updates(info: dict) -> str:
    return f"""You are writing a special education updates/news page for {info['name']}, a NY school district.
District: {info['name']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY raw JSON. No markdown. No explanation.

{{
  "meta_description": "...",
  "hero_sub": "...",
  "intro_p": "...",
  "why_track_h2": "...",
  "why_track_p": "...",
  "things_to_track": ["...", "...", "...", "...", "..."],
  "official_sources": [
    {{"name": "...", "url": "https://...", "desc": "..."}},
    {{"name": "...", "url": "https://...", "desc": "..."}}
  ],
  "cta_p": "..."
}}

meta_description: 140-160 chars. Include {info['name']}, special education news, policy updates. No "Find".
hero_sub: 1 sentence about staying current on {info['name']} special education changes.
intro_p: 2 sentences — policies change, budgets shift, parents need to stay informed.

why_track_h2: 5-8 words
why_track_p: 2-3 sentences about why monitoring {info['name']} BOE meetings and state updates matters
  for parents of students with IEPs. Mention budget votes and policy changes.

things_to_track: 5 specific things a {info['name']} parent should monitor.
  Examples: BOE meeting minutes, annual budget proposals, NYSED corrective action plans,
  CSE staffing changes, district special ed audit results.

official_sources: 2 REAL sources with correct URLs.
  Must include: {info['name']} official district website OR {info['county']} County BOCES website.
  Second source: NYSED or a county-specific resource. Use real verified URLs only.

cta_p: 1-2 sentences. Encourage checking back or following official sources.
"""


def prompt_partners(info: dict) -> str:
    return f"""You are writing a providers/partners page for NY special education parents.
District: {info['name']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY raw JSON. No markdown.

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

meta_description: 140-160 chars. Mention {info['name']}, CSE advocates, local providers. No "Find".

insight_h4: 6-10 words, mention {info['name']}
insight_p: 2-3 sentences about free services available. 
  {info['type']} context: {'bilingual evals, autism support, MDR help' if info['type'] == 'urban' else 'LRE placement, IEE rights, transition planning'}

process_items: 3 items.
  h4: 3-5 words
  p: max 15 words
  Tailor to {info['type']}: 
  {'Urban: evaluation delays, bilingual CSE rights, discipline/MDR issues' if info['type'] == 'urban' else 'Suburban: LRE placement fights, IEE at district expense, transition to adulthood'}

local_resources: exactly 2 REAL organizations serving {info['city']} or {info['county']} County.
  Use REAL working URLs. Options: county Arc chapter, SETRC offices, legal aid societies,
  university disability clinics, hospital neuropsychology centers.
  Do NOT include: DRNY, Advocates for Children, INCLUDEnyc, NYSED (already in template).
  For Rockland County / East Ramapo: consider RCASA, Jawonio, Legal Services of the Hudson Valley.
  For Suffolk County: consider ACLD (Association for Children with Learning Disabilities), 
    Community Action Southold Town, Suffolk County Arc.
  For Monroe County / Greece: consider CP Rochester, Advocacy for Inclusion, Monroe County Arc.
"""


def prompt_guide(info: dict) -> str:
    return f"""You are writing a parent advocacy guide page for NY special education parents.
District: {info['name']} | County: {info['county']} | Type: {info['type']}
Context: {info['notes']}

Return ONLY raw JSON. No markdown.

{{
  "meta_title": "...",
  "meta_description": "...",
  "intro_p": "...",
  "sections": [
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}},
    {{"h2": "...", "content_html": "..."}}
  ],
  "faq": [
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}},
    {{"q": "...", "a": "..."}}
  ],
  "cta_p": "..."
}}

meta_title: max 60 chars. Format: "CSE Advocacy Guide for {info['name']} Parents | NY Special Ed"
meta_description: 140-160 chars. Include {info['name']}, advocacy, IEP rights, CSE process.

intro_p: 2-3 sentences. Warm opening for a {info['type']} district parent.
  Reference {info['county']} County CSE process. Acknowledge what makes {info['name']} specific.

sections: exactly 4. Use <p>, <ul>, <li>, <strong>, <ol> only in content_html.
Topics:
  1. Understanding the CSE process in {info['name']} — what's different locally
  2. Building your case before the CSE meeting — records, prior data, independent evaluations
  3. At the table — how to advocate effectively without burning bridges
  4. When to escalate — NYSED complaints, impartial hearings, and legal options in NY

faq: 4 questions a {info['name']} parent would search for. 
  Include {info['name']} in at least 3 answers.
  Cover: evaluation timelines, IEE rights, dispute process, local advocacy resources.
  All answers reflect NY law (Part 200, IDEA). NO Texas/ARD references.

cta_p: 1-2 sentences. Transition to partners.html for local professional help.
"""


# ══════════════════════════════════════════════════════════════
#  PAGE BUILDERS
# ══════════════════════════════════════════════════════════════

def build_index_page(slug: str, info: dict, data: dict) -> str:
    silo = build_silo_nav(info['name'], slug, "index")
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

    stats_html = ""
    for s in data.get("quick_stats", []):
        stats_html += f"""        <div class="stat-item">
          <div class="stat-value">{s['value']}</div>
          <div class="stat-label">{s['label']}</div>
        </div>\n"""

    canonical = f"{SITE_BASE_URL}/districts/{slug}/index.html"
    return f"""<!DOCTYPE html>
<html lang="en">
{head(f"Special Education Resources — {info['name']} | NY Special Ed", data['meta_description'], canonical)}
<body>
{MARKER_INDEX}
{std_header()}
{page_hero(info['name'], info['name'], f"Special Education Resources<br/>in {info['name']}", data['hero_sub'])}

<main>
  <div class="container">

    {silo}

    {trust_anchor()}

    <div class="district-intro">
      <h2>{data['intro_h2']}</h2>
      <p>{data['intro_p']}</p>
    </div>

    <!-- QUICK STATS -->
    <div class="quick-stats-bar">
{stats_html}    </div>

    <!-- LOCAL NOTE -->
    <div class="insight-box" style="margin-bottom:40px;">
      <div class="insight-icon"><i class="fas fa-map-marker-alt"></i></div>
      <div class="insight-text">
        <h4>About Special Ed in {info['name']}</h4>
        <p>{data['local_note']}</p>
      </div>
    </div>

    <!-- HUB GRID -->
    <div class="section-title-row">
      <h2>What Do You Need Help With?</h2>
    </div>
    <div class="hub-grid">
{cards_html}      <a class="hub-card" href="parent-advocacy-guide.html">
        <div class="hub-card-icon"><i class="fas fa-book-open-reader"></i></div>
        <div class="hub-card-body">
          <h3>Advocacy Guide</h3>
          <p>Step-by-step strategies for advocating at the CSE table in {info['name']}.</p>
          <span class="hub-card-cta">Read the guide &rarr;</span>
        </div>
      </a>
      <a class="hub-card" href="leadership-directory.html">
        <div class="hub-card-icon"><i class="fas fa-address-book"></i></div>
        <div class="hub-card-body">
          <h3>District Contacts</h3>
          <p>Who to call in {info['name']}'s special education office — and what to say.</p>
          <span class="hub-card-cta">Find contacts &rarr;</span>
        </div>
      </a>
    </div>

  </div>
</main>

{std_footer()}
</body>
</html>"""


def build_content_page(slug: str, info: dict, data: dict,
                       page_key: str, marker: str,
                       title: str, h1: str,
                       extra_elements: str = "") -> str:
    silo = build_silo_nav(info['name'], slug, page_key)
    sections_html = ""
    for sec in data.get("sections", []):
        sections_html += f"""
    <div class="content-section">
      <h2>{sec['h2']}</h2>
      {sec['content_html']}
    </div>"""

    faq_html = ""
    for item in data.get("faq", []):
        faq_html += f"""
      <div class="faq-item">
        <h3>{item['q']}</h3>
        <p>{item['a']}</p>
      </div>"""

    canonical = f"{SITE_BASE_URL}/districts/{slug}/{page_key}.html"

    # Build page_title from the data or passed title
    page_title = data.get('meta_title', f"{title} — {info['name']} | NY Special Ed")

    return f"""<!DOCTYPE html>
<html lang="en">
{head(page_title, data['meta_description'], canonical)}
<body>
{marker}
{std_header()}
{page_hero(info['name'], info['name'], h1, data['hero_sub'])}

<main>
  <div class="container">

    {silo}
    {trust_anchor()}

    <div class="content-intro">
      <p>{data.get('intro_p', '')}</p>
    </div>

    {sections_html}

    {extra_elements}

    <div class="faq-section" style="margin-top:48px;">
      <div class="section-title-row">
        <h2>Frequently Asked Questions</h2>
        <span>{info['name']} parents ask</span>
      </div>
      {faq_html}
    </div>

    <div class="insight-box" style="margin-top:40px;">
      <div class="insight-icon"><i class="fas fa-hands-helping"></i></div>
      <div class="insight-text">
        <h4>Need local help?</h4>
        <p>Browse attorneys, advocates, and evaluators serving {info['name']}. <a href="partners.html">Find local providers &rarr;</a></p>
      </div>
    </div>

  </div>
</main>

{std_footer()}
</body>
</html>"""


def build_cse_page(slug: str, info: dict, data: dict) -> str:
    checklist_items = "".join(
        f"<li>{item}</li>\n" for item in data.get("checklist", [])
    )
    checklist_html = f"""
    <div class="content-section checklist-section">
      <h2>Before Your CSE Meeting — Checklist</h2>
      <ul class="checklist">
{checklist_items}      </ul>
    </div>""" if checklist_items else ""

    return build_content_page(
        slug, info, data, "cse", MARKER_CSE,
        f"CSE Meeting Guide — {info['name']} | NY Special Ed",
        f"CSE Meeting Guide<br/>for {info['name']} Parents",
        extra_elements=checklist_html,
    )


def build_discipline_page(slug: str, info: dict, data: dict) -> str:
    warning_items = "".join(
        f"<li>{w}</li>\n" for w in data.get("warning_signs", [])
    )
    warning_html = f"""
    <div class="content-section warning-section">
      <h2>When to Get Legal Help Immediately</h2>
      <ul class="warning-list">
{warning_items}      </ul>
      <p><a href="partners.html">Find a special education attorney in {info['name']} &rarr;</a></p>
    </div>""" if warning_items else ""

    return build_content_page(
        slug, info, data, "disc", MARKER_DISC,
        f"Discipline Rights — {info['name']} | NY Special Ed",
        f"Discipline Rights &amp; Impartial Hearings<br/>in {info['name']}",
        extra_elements=warning_html,
    )


def build_directory_page(slug: str, info: dict, data: dict) -> str:
    silo = build_silo_nav(info['name'], slug, "contacts")
    contacts_html = ""
    for c in data.get("key_contacts", []):
        contacts_html += f"""      <div class="contact-card">
        <div class="contact-role"><i class="fas fa-user-tie"></i> {c['role']}</div>
        <div class="contact-note">{c['note']}</div>
      </div>\n"""

    canonical = f"{SITE_BASE_URL}/districts/{slug}/leadership-directory.html"
    return f"""<!DOCTYPE html>
<html lang="en">
{head(f"Special Education Contacts — {info['name']} | NY Special Ed", data['meta_description'], canonical)}
<body>
{MARKER_DIR}
{std_header()}
{page_hero(info['name'], info['name'], f"Special Education Contacts<br/>in {info['name']}", data['hero_sub'])}

<main>
  <div class="container">
    {silo}
    {trust_anchor()}

    <div class="content-intro">
      <p>{data.get('intro_p', '')}</p>
    </div>

    <div class="section-title-row">
      <h2>Key Roles in {info['name']}'s Special Education Department</h2>
    </div>
    <div class="contact-grid">
{contacts_html}    </div>

    <div class="content-section">
      <h2>How to Reach District Staff Effectively</h2>
      <p>{data.get('how_to_p', '')}</p>
    </div>

    <div class="content-section">
      <h2>When the District Doesn't Respond — NYSED Complaints</h2>
      <p>{data.get('nysed_complaint_p', '')}</p>
      <p><a href="https://www.nysed.gov/special-education/state-complaints" target="_blank" rel="noopener">
        File a State Complaint with NYSED &rarr;</a></p>
    </div>

    <div class="insight-box" style="margin-top:40px;">
      <div class="insight-icon"><i class="fas fa-hands-helping"></i></div>
      <div class="insight-text">
        <h4>Need an advocate at the table?</h4>
        <p>Find local advocates and attorneys who can attend CSE meetings with you.
          <a href="partners.html">Browse {info['name']} providers &rarr;</a></p>
      </div>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def build_updates_page(slug: str, info: dict, data: dict) -> str:
    silo = build_silo_nav(info['name'], slug, "updates")
    track_items = "".join(f"<li>{t}</li>\n" for t in data.get("things_to_track", []))

    sources_html = ""
    for s in data.get("official_sources", []):
        sources_html += f"""      <a class="free-card" href="{s['url']}" target="_blank" rel="noopener">
        <div class="free-card-icon"><i class="fas fa-external-link-alt"></i></div>
        <div class="free-card-text"><strong>{s['name']}</strong><span>{s['desc']}</span></div>
        <i class="fas fa-external-link-alt free-card-arrow"></i>
      </a>\n"""

    canonical = f"{SITE_BASE_URL}/districts/{slug}/special-ed-updates.html"
    return f"""<!DOCTYPE html>
<html lang="en">
{head(f"Special Education Updates — {info['name']} | NY Special Ed", data['meta_description'], canonical)}
<body>
{MARKER_UPDATES}
{std_header()}
{page_hero(info['name'], info['name'], f"Special Education Updates<br/>for {info['name']}", data['hero_sub'])}

<main>
  <div class="container">
    {silo}
    {trust_anchor()}

    <div class="content-intro">
      <p>{data.get('intro_p', '')}</p>
    </div>

    <div class="content-section">
      <h2>{data.get('why_track_h2', 'Why Staying Informed Matters')}</h2>
      <p>{data.get('why_track_p', '')}</p>
    </div>

    <div class="content-section">
      <h2>What to Monitor in {info['name']}</h2>
      <ul>
{track_items}      </ul>
    </div>

    <div class="content-section">
      <h2>Official Sources</h2>
      <div class="free-cards-grid">
{sources_html}      </div>
    </div>

    <div class="insight-box" style="margin-top:40px;">
      <div class="insight-icon"><i class="fas fa-bell"></i></div>
      <div class="insight-text">
        <h4>Staying ahead in {info['name']}</h4>
        <p>{data.get('cta_p', 'Check the official district website regularly for special education updates.')}</p>
      </div>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def build_partners_page(slug: str, info: dict, data: dict) -> str:
    silo = build_silo_nav(info['name'], slug, "partners")
    proc_html = ""
    for i, item in enumerate(data.get("process_items", []), 1):
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

    canonical = f"{SITE_BASE_URL}/districts/{slug}/partners.html"
    return f"""<!DOCTYPE html>
<html lang="en">
{head(f"Special Education Providers & Support — {info['name']} | NY Special Ed", data['meta_description'], canonical,
      extra_css='\n  <link href="/styles/partners.css" rel="stylesheet"/>')}
<body>
{MARKER_PARTNERS}
{std_header()}
{page_hero(info['name'], info['name'],
           f"Special Education Providers<br/>in {info['name']}",
           f"Connect with local advocates, attorneys, and evaluators who know NY special education law — and the CSE process in {info['name']} specifically.")}

<main>
  <div class="container">
    {silo}
    {trust_anchor()}

    <!-- FEATURED AD SLOT -->
    <div class="featured-ad-zone">
      <span class="ad-badge-premium">District Exclusive</span>
      <div class="ad-logo-box"><i class="fas fa-building"></i><span>Your Logo</span></div>
      <div class="ad-content">
        <span class="label label-gold">Featured Partner</span>
        <h3>Position your practice as the trusted authority in {info['name']}</h3>
        <p>Reach high-intent parents seeking independent evaluations, neuropsychological testing, or CSE advocacy — right when they need it most. One exclusive listing per district.</p>
        <div class="ad-tags">
          <span class="ad-tag">IEE Evaluations</span>
          <span class="ad-tag">CSE Advocacy</span>
          <span class="ad-tag">Neuropsych Testing</span>
          <span class="ad-tag">Legal Support</span>
        </div>
      </div>
      <a class="btn-claim" href="{ADVERTISE_URL}">Reserve This Spot <i class="fas fa-arrow-right" style="font-size:.75rem;"></i></a>
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
      <h2>Navigating Special Ed in {info['name']}</h2>
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
        <p>Be the first advocate parents call when they hit a wall at the CSE table. Exclusive to this category in {info['name']}.</p>
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
        <p>Position your firm as the go-to legal resource for families in {info['name']} navigating due process or NYSED complaints.</p>
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
        <p>Reach parents in {info['name']} seeking an independent second opinion after the district's evaluation.</p>
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
        <p>Connect with families whose children need private therapy to supplement their IEP services in {info['name']}.</p>
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
        <p>We are the only independent resource hub for New York special education parents. Our {info['name']} pages capture high-intent traffic from families actively seeking evaluations and legal support — often within hours of a CSE meeting.</p>
      </div>
      <a href="{ADVERTISE_URL}" class="btn-partner">Become a Partner <i class="fas fa-arrow-right" style="font-size:.75rem;"></i></a>
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
        <div class="tier-header"><i class="fas fa-map-marker-alt"></i> Local Resources &mdash; {info['name']} Area</div>
        <div class="tier-body">
{local_html}        </div>
      </div>
    </section>
  </div>
</main>
{std_footer()}
</body>
</html>"""


def build_guide_page(slug: str, info: dict, data: dict) -> str:
    silo = build_silo_nav(info['name'], slug, "guide")
    sections_html = ""
    for sec in data.get("sections", []):
        sections_html += f"""
    <div class="content-section">
      <h2>{sec['h2']}</h2>
      {sec['content_html']}
    </div>"""

    faq_html = ""
    for item in data.get("faq", []):
        faq_html += f"""
      <div class="faq-item">
        <h3>{item['q']}</h3>
        <p>{item['a']}</p>
      </div>"""

    canonical = f"{SITE_BASE_URL}/districts/{slug}/parent-advocacy-guide.html"
    meta_title = data.get("meta_title", f"CSE Advocacy Guide — {info['name']} | NY Special Ed")
    return f"""<!DOCTYPE html>
<html lang="en">
{head(meta_title, data['meta_description'], canonical)}
<body>
{MARKER_GUIDE}
{std_header()}
{page_hero(info['name'], info['name'],
           f"Parent Advocacy Guide<br/>for {info['name']}",
           f"Practical strategies for navigating the CSE process, understanding your rights, and advocating effectively for your child in {info['name']}.")}

<main>
  <div class="container">
    {silo}
    {trust_anchor()}

    <div class="content-intro">
      <p>{data.get('intro_p', '')}</p>
    </div>

    {sections_html}

    <div class="faq-section" style="margin-top:48px;">
      <div class="section-title-row">
        <h2>Frequently Asked Questions</h2>
        <span>{info['name']} parents ask</span>
      </div>
      {faq_html}
    </div>

    <div class="insight-box" style="margin-top:48px;">
      <div class="insight-icon"><i class="fas fa-hands-helping"></i></div>
      <div class="insight-text">
        <h4>Need a local advocate or evaluator?</h4>
        <p>{data.get('cta_p', '')} <a href="partners.html">Browse local providers in {info['name']} &rarr;</a></p>
      </div>
    </div>
  </div>
</main>
{std_footer()}
</body>
</html>"""


# ══════════════════════════════════════════════════════════════
#  INDEX PAGE UPDATE
# ══════════════════════════════════════════════════════════════

def update_district_index(districts_path: Path, new_slugs: list, dry_run: bool):
    """
    Finds the districts listing index.html and adds cards for new districts.
    Looks for common patterns: a <ul class="district-list">, .hub-grid, or table.
    Appends new cards before the closing tag if pattern found.
    """
    # Try common index file locations
    candidates = [
        districts_path / "index.html",
        districts_path.parent / "districts.html",
        districts_path.parent / "index.html",
    ]
    index_file = next((p for p in candidates if p.exists()), None)

    if not index_file:
        log.warning("  INDEX UPDATE SKIP — could not locate districts index.html")
        log.warning(f"  Searched: {[str(p) for p in candidates]}")
        return

    log.info(f"  Updating index: {index_file}")
    html = index_file.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")

    for slug in new_slugs:
        info = NEW_DISTRICTS[slug]

        # Skip if already present
        if slug in html:
            log.info(f"  INDEX: {slug} already found in index — skipping")
            continue

        # Build a new district card
        new_card_html = f"""
      <!-- {info['name']} — added by build_new_ny_districts.py -->
      <div class="district-card">
        <div class="district-card-header">
          <span class="district-region-badge">{info['region']}</span>
          <h3><a href="{slug}/index.html">{info['name']}</a></h3>
          <p class="district-county">{info['county']} County</p>
        </div>
        <div class="district-card-body">
          <p>Special education resources, CSE meeting guides, and local provider directory for {info['name']} families.</p>
        </div>
        <a href="{slug}/index.html" class="district-card-cta">View Resources &rarr;</a>
      </div>"""

        new_card = BeautifulSoup(new_card_html, "lxml")

        # Try to find insertion point — hub-grid, district-grid, district-list, or district-cards
        container = (
            soup.find(class_="hub-grid") or
            soup.find(class_="district-grid") or
            soup.find(class_="district-cards") or
            soup.find(id="district-list") or
            soup.find("ul", class_="district-list") or
            soup.find(class_="districts-container")
        )

        if container:
            container.append(new_card)
            log.info(f"  INDEX: Added card for {info['name']} to existing container")
        else:
            # Fallback: append a comment before </body> so it's easy to find
            log.warning(f"  INDEX: No container found — appending {info['name']} card before </body>")
            body = soup.find("body")
            if body:
                body.append(new_card)

    if dry_run:
        log.info("  [DRY RUN] Would update district index — no write")
    else:
        index_file.write_text(str(soup), encoding="utf-8")
        log.info(f"  ✓ Updated district index: {index_file.name}")


# ══════════════════════════════════════════════════════════════
#  DISTRICT PROCESSOR
# ══════════════════════════════════════════════════════════════

PAGE_SPECS = [
    # (filename,               marker,           prompt_fn,         build_fn,        step_label)
    ("index.html",             MARKER_INDEX,     prompt_index,      None,            "Hub index"),
    ("cse-meeting-guide.html", MARKER_CSE,       prompt_cse,        None,            "CSE guide"),
    ("evaluation-process.html",MARKER_EVAL,      prompt_eval,       None,            "Evaluation"),
    ("discipline-rights.html", MARKER_DISC,      prompt_discipline, None,            "Discipline"),
    ("leadership-directory.html",MARKER_DIR,     prompt_directory,  None,            "Directory"),
    ("special-ed-updates.html",MARKER_UPDATES,   prompt_updates,    None,            "Updates"),
    ("partners.html",          MARKER_PARTNERS,  prompt_partners,   None,            "Partners"),
    ("parent-advocacy-guide.html",MARKER_GUIDE,  prompt_guide,      None,            "Advocacy guide"),
]

BUILD_FNS = {
    "index.html":                  build_index_page,
    "cse-meeting-guide.html":      build_cse_page,
    "evaluation-process.html":     lambda s,i,d: build_content_page(
                                       s,i,d,"eval",MARKER_EVAL,
                                       f"Evaluation Rights — {i['name']} | NY Special Ed",
                                       f"Requesting an Evaluation<br/>in {i['name']}"),
    "discipline-rights.html":      build_discipline_page,
    "leadership-directory.html":   build_directory_page,
    "special-ed-updates.html":     build_updates_page,
    "partners.html":               build_partners_page,
    "parent-advocacy-guide.html":  build_guide_page,
}


def process_district(slug: str, info: dict, model, args) -> bool:
    log.info(f"══ {info['name']} ({slug}) ════════════════════════")
    districts_path = Path(args.districts_dir)
    folder = districts_path / slug

    if args.dry_run:
        log.info(f"  [DRY RUN] Would create folder: {folder}")
    else:
        folder.mkdir(parents=True, exist_ok=True)
        log.info(f"  Folder: {folder}")

    success_count = 0

    for filename, marker, prompt_fn, _, label in PAGE_SPECS:
        filepath = folder / filename
        build_fn  = BUILD_FNS[filename]

        # Skip if already built
        if not args.no_skip and filepath.exists():
            existing = filepath.read_text(encoding="utf-8", errors="replace")
            if marker in existing:
                log.info(f"  SKIP {label} — already built")
                success_count += 1
                continue

        log.info(f"  Generating {label}...")
        data = call_vertex(model, prompt_fn(info), info['name'], label)
        if not data:
            log.error(f"  ✗ FAILED {label} — Vertex returned no data")
            continue

        html = build_fn(slug, info, data)

        if args.dry_run:
            log.info(f"  [DRY RUN] Would write {filename} ({len(html):,} chars)")
        else:
            filepath.write_text(html, encoding="utf-8")
            log.info(f"  ✓ Wrote {filename}")

        success_count += 1

    log.info(f"  {success_count}/{len(PAGE_SPECS)} pages complete for {info['name']}")
    return success_count == len(PAGE_SPECS)


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Build new NY special education district pages")
    parser.add_argument("--districts-dir", default=DISTRICTS_DIR,
                        help="Path to districts folder")
    parser.add_argument("--district",       type=str, default=None,
                        help="Build single district by slug (e.g. sachem-csd)")
    parser.add_argument("--dry-run",        action="store_true",
                        help="Preview only — no files written")
    parser.add_argument("--no-skip",        action="store_true",
                        help="Rebuild even if page already exists")
    parser.add_argument("--skip-index-update", action="store_true",
                        help="Do not update the districts index page")
    args = parser.parse_args()

    # Validate districts dir
    districts_path = Path(args.districts_dir)
    if not args.dry_run and not districts_path.exists():
        log.error(f"Districts directory not found: {args.districts_dir}")
        sys.exit(1)

    # Filter to requested district if --district passed
    if args.district:
        if args.district not in NEW_DISTRICTS:
            log.error(f"Unknown district slug: {args.district}")
            log.error(f"Available: {list(NEW_DISTRICTS.keys())}")
            sys.exit(1)
        to_build = {args.district: NEW_DISTRICTS[args.district]}
    else:
        to_build = NEW_DISTRICTS

    log.info(f"Districts to build: {list(to_build.keys())}")
    log.info(f"Output path: {args.districts_dir}")
    if args.dry_run:
        log.info("DRY RUN MODE — no files will be written")

    # Init Vertex AI
    log.info(f"Vertex AI init — project={GCP_PROJECT_ID}  model={GEMINI_MODEL}")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    model = GenerativeModel(GEMINI_MODEL)

    # Build each district
    built_slugs = []
    for slug, info in to_build.items():
        try:
            ok = process_district(slug, info, model, args)
            if ok:
                built_slugs.append(slug)
        except Exception as e:
            log.error(f"UNHANDLED ERROR for {slug}: {e}")
            import traceback; traceback.print_exc()

    # Update the main district index
    if not args.skip_index_update and built_slugs:
        log.info("══ Updating district index page ════════════════")
        update_district_index(districts_path, built_slugs, args.dry_run)

    log.info("═" * 60)
    log.info(f"Complete. Built {len(built_slugs)}/{len(to_build)} districts.")
    if len(built_slugs) < len(to_build):
        failed = [s for s in to_build if s not in built_slugs]
        log.warning(f"Failed or incomplete: {failed}")


if __name__ == "__main__":
    main()