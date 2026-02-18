import os
import pandas as pd
import json
import shutil
import time
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting

# ==========================================
# 🛑 CONFIGURATION
# ==========================================
PROJECT_ID = "ny-build"
LOCATION = "us-central1"
# ==========================================

print(f"🔌 Connecting to Google Cloud Project: {PROJECT_ID}...")
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"❌ AUTH ERROR: {e}")
    exit()

model = GenerativeModel("gemini-1.5-flash-001")

def load_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Could not find {path}")
        exit()

# Load Components
try:
    NAVBAR_HTML = load_file('components/components-navbar.html')
    FOOTER_HTML = load_file('components/components-footer.html')
except SystemExit:
    print("⚠️  MISSING COMPONENTS: Check 'components/' folder.")
    exit()

CSS_LINKS = """
<link rel="stylesheet" href="/styles/global.css">
<link rel="stylesheet" href="/styles/styles-nav-footer.css">
"""

# Load Data
print("...Loading Data...")
try:
    nyc_df = pd.read_csv('nyc_districts.csv') 
    state_df = pd.read_csv('nys_districts.csv')
    with open('cse_directory.json', 'r') as f:
        cse_lookup = json.load(f)
    try:
        nysed_contacts = pd.read_csv('nysed_contacts.csv', encoding='latin1')
        nysed_contacts.columns = nysed_contacts.columns.str.strip()
    except Exception as e:
        print(f"❌ Error reading nysed_contacts.csv: {e}")
        exit()
except FileNotFoundError as e:
    print(f"❌ DATA ERROR: {e}")
    exit()

def setup_directories():
    if os.path.exists('output'):
        try:
            shutil.rmtree('output')
        except:
            pass
    os.makedirs('output/styles', exist_ok=True)
    try:
        shutil.copy('styles/styles-nav-footer.css', 'output/styles/')
        shutil.copy('styles/global.css', 'output/styles/')
    except:
        pass

# ==========================================
# 📄 THE SUB-PAGE TEMPLATES (The "Rooms")
# ==========================================

# 1. LEADERSHIP DIRECTORY TEMPLATE
LEADERSHIP_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Special Education Contacts: {district_name}</title>
  <meta name="description" content="Direct phone numbers and emails for {district_name} Committee on Special Education (CSE) and leadership.">
  {css_links}
</head>
<body>
  {navbar}
  <main class="container">
    <div class="aeo-authority-block">
        <a href="./">← Back to {district_name} Hub</a>
    </div>
    <h1>{district_name} Leadership Directory</h1>
    <p class="lead">Who to contact for IEPs, Evaluations, and escalations.</p>
    
    <div class="contact-grid">
        {contacts_html}
    </div>

    <div class="alert-box" style="background: #fff3cd; padding: 20px; margin-top: 30px; border-radius: 8px;">
        <strong>⚠️ Escalation Tip:</strong> If you do not receive a response within 48 hours, document your attempt and escalate to the {escalation_target}.
    </div>
  </main>
  {footer}
</body>
</html>"""

# 2. CSE MEETING GUIDE (Equivalent to ARD)
CSE_GUIDE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CSE Meeting Guide for {district_name}</title>
  <meta name="description" content="What to expect at a Committee on Special Education (CSE) meeting in {district_name}. Your rights and agenda.">
  {css_links}
</head>
<body>
  {navbar}
  <main class="container">
    <div class="aeo-authority-block">
        <a href="./">← Back to {district_name} Hub</a>
    </div>
    <h1>CSE Meeting Guide: {district_name}</h1>
    <p class="lead">Navigating your Annual Review or Initial Eligibility meeting.</p>
    
    <h2>Who Attends?</h2>
    <ul>
        <li><strong>You (The Parent):</strong> You are an equal member of the team.</li>
        <li><strong>District Representative:</strong> Someone qualified to authorize resources (often the {leader_title}).</li>
        <li><strong>School Psychologist:</strong> To interpret evaluation data.</li>
        <li><strong>Special Education Teacher:</strong> To discuss classroom performance.</li>
    </ul>

    <h2>The Agenda</h2>
    <ol>
        <li><strong>Introduction:</strong> Verify all required members are present.</li>
        <li><strong>Present Levels (PLOP):</strong> How is your child doing right now?</li>
        <li><strong>Goals:</strong> What will they achieve in the next 12 months?</li>
        <li><strong>Services & Placement:</strong> ICT, 12:1:1, or General Ed?</li>
    </ol>
    
    <div class="cta-box">
        <h3>Need a Checklist?</h3>
        <p>Don't walk in unprepared. Download our NY CSE Meeting Checklist.</p>
        <a href="/resources/cse-meeting-checklist.pdf" class="btn">Download Free PDF</a>
    </div>
  </main>
  {footer}
</body>
</html>"""

# 3. EVALUATION GUIDE
EVAL_GUIDE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Requesting an Evaluation in {district_name}</title>
  <meta name="description" content="How to request a special education evaluation in {district_name}. Timelines and process.">
  {css_links}
</head>
<body>
  {navbar}
  <main class="container">
    <div class="aeo-authority-block">
        <a href="./">← Back to {district_name} Hub</a>
    </div>
    <h1>Evaluation Process: {district_name}</h1>
    
    <div class="timeline-box" style="border-left: 4px solid #0056b3; padding-left: 20px;">
        <h3>The 60-Day Rule</h3>
        <p>In New York State, the district has <strong>60 calendar days</strong> from the moment you sign consent to complete evaluations and hold the eligibility meeting.</p>
    </div>

    <h2>Step 1: The Referral</h2>
    <p>You must submit a written letter to the {leader_title}. Do not just ask verbally.</p>
    <p><strong>Send to:</strong> {district_name} CSE Office<br>
    <strong>Email/Fax:</strong> {contact_phone} (Call to confirm fax number)</p>

    <h2>Step 2: Consent</h2>
    <p>The district will send you a "Consent to Evaluate" form. The clock does not start until you sign and return this.</p>
  </main>
  {footer}
</body>
</html>"""

# 4. DISCIPLINE / DISPUTE GUIDE
DISCIPLINE_GUIDE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Discipline & Disputes in {district_name}</title>
  <meta name="description" content="Manifestation Determination (MDR) and Superintendent Hearings in {district_name}.">
  {css_links}
</head>
<body>
  {navbar}
  <main class="container">
    <div class="aeo-authority-block">
        <a href="./">← Back to {district_name} Hub</a>
    </div>
    <h1>Discipline & Rights: {district_name}</h1>
    
    <h2>Suspensions Over 10 Days</h2>
    <p>If your child is suspended for more than 10 days (consecutive or cumulative), {district_name} must hold a <strong>Manifestation Determination Review (MDR)</strong>.</p>
    
    <h3>The Golden Rule</h3>
    <p>They cannot punish your child for behavior that is a result of their disability.</p>

    <h2>Filing a Complaint</h2>
    <p>If you disagree with a decision, you have the right to:</p>
    <ul>
        <li>File a <strong>State Complaint</strong> with NYSED.</li>
        <li>Request <strong>Mediation</strong>.</li>
        <li>File for an <strong>Impartial Hearing</strong> (Due Process).</li>
    </ul>
  </main>
  {footer}
</body>
</html>"""

# ==========================================
# 🧠 LOGIC & GENERATOR
# ==========================================

def get_nyc_contact_data(district_str):
    dist_num = ''.join(filter(str.isdigit, str(district_str)))
    if dist_num in cse_lookup:
        data = cse_lookup[dist_num]
        return {
            "html": f"""
            <div class="contact-box">
                <h3>{data['region']} (Serving District {dist_num})</h3>
                <div class="contact-item"><strong>Address:</strong> {data['address']}</div>
                <div class="contact-item"><strong>Phone:</strong> <a href="tel:{data['phone']}">{data['phone']}</a></div>
            </div>""",
            "phone": data['phone'],
            "leader": "CSE Chairperson",
            "escalation": "NYC DOE Central Region Office"
        }
    return {"html": "", "phone": "311", "leader": "CSE Chairperson", "escalation": "NYC DOE"}

def get_state_contact_data(district_name):
    match = nysed_contacts[nysed_contacts['District'].astype(str).str.contains(district_name, case=False, na=False)]
    if not match.empty:
        row = match.iloc[0]
        phone = row.get('phone', 'N/A')
        address = row.get('address', '')
        return {
            "html": f"""
            <div class="contact-box">
                <h3>Special Education Office</h3>
                <div class="contact-item"><strong>Address:</strong> {address}</div>
                <div class="contact-item"><strong>Phone:</strong> <a href="tel:{phone}">{phone}</a></div>
            </div>""",
            "phone": phone,
            "leader": "Director of Special Education",
            "escalation": "NYSED Special Education QA (SEQA)"
        }
    return {"html": "", "phone": "N/A", "leader": "Director of Special Education", "escalation": "NYSED"}

def generate_district_ecosystem(row, type="NYC"):
    district_name = row['District']
    slug = row['URL Slug']
    
    print(f"🚀 Generating Ecosystem for: {district_name}...")

    # 1. Get Contact Data
    if type == "NYC":
        contact_data = get_nyc_contact_data(district_name)
    else:
        contact_data = get_state_contact_data(district_name)

    # 2. Generate the 4 SUB-PAGES
    output_path = f"output{slug}"
    os.makedirs(output_path, exist_ok=True)

    # Write Leadership Page
    with open(f"{output_path}/leadership-directory.html", "w", encoding="utf-8") as f:
        f.write(LEADERSHIP_TEMPLATE.format(
            district_name=district_name,
            contacts_html=contact_data['html'],
            escalation_target=contact_data['escalation'],
            css_links=CSS_LINKS, navbar=NAVBAR_HTML, footer=FOOTER_HTML
        ))

    # Write CSE Guide
    with open(f"{output_path}/cse-meeting-guide.html", "w", encoding="utf-8") as f:
        f.write(CSE_GUIDE_TEMPLATE.format(
            district_name=district_name,
            leader_title=contact_data['leader'],
            css_links=CSS_LINKS, navbar=NAVBAR_HTML, footer=FOOTER_HTML
        ))

    # Write Eval Guide
    with open(f"{output_path}/evaluation-process.html", "w", encoding="utf-8") as f:
        f.write(EVAL_GUIDE_TEMPLATE.format(
            district_name=district_name,
            leader_title=contact_data['leader'],
            contact_phone=contact_data['phone'],
            css_links=CSS_LINKS, navbar=NAVBAR_HTML, footer=FOOTER_HTML
        ))
    
    # Write Discipline Guide
    with open(f"{output_path}/discipline-rights.html", "w", encoding="utf-8") as f:
        f.write(DISCIPLINE_GUIDE_TEMPLATE.format(
            district_name=district_name,
            css_links=CSS_LINKS, navbar=NAVBAR_HTML, footer=FOOTER_HTML
        ))

    # 3. Generate the MAIN INDEX PAGE (The Hub)
    # We update the links to point to these new local files
    
    # Call AI for the Hub content
    prompt = f"""
    Write HTML for {district_name} (NY).
    Context: {row.get('Key Neighborhoods', 'NY State')}. Focus: {row.get('Key Special Ed Focus', 'General')}.
    
    JSON OUTPUT:
    1. "authority_summary": 2 sentences on district compliance.
    2. "faq_html": 3 FAQs.
    3. "schema_json": JSON-LD.
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        ai_data = json.loads(response.text)
    except:
        ai_data = {"authority_summary": "Follows NYSED Part 200.", "faq_html": "", "schema_json": "{}"}

    # The HUB Template (Updated with Local Links)
    HUB_TEMPLATE = """<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>{district_name} Special Education Hub</title>
      <meta name="description" content="Complete guide to Special Education in {district_name}. Contacts, CSE meetings, and evaluations.">
      {css_links}
      <script type="application/ld+json">{schema_json}</script>
    </head>
    <body>
      {navbar}
      <main class="container">
        <div class="aeo-authority-block" style="background: #f0f7ff; padding: 20px; border-left: 5px solid #0056b3; margin: 20px 0;">
            {authority_summary}
        </div>
        <h1>{district_name} Special Education Hub</h1>
        
        <div class="hub-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 40px 0;">
            
            <a href="./leadership-directory.html" class="hub-card" style="padding: 20px; border: 1px solid #ddd; border-radius: 8px; text-decoration: none; color: inherit; display: block;">
                <h3 style="color: #0056b3; margin-top: 0;">📞 Leadership Directory</h3>
                <p>Phone numbers and emails for {leader_title} and CSE offices.</p>
            </a>

            <a href="./cse-meeting-guide.html" class="hub-card" style="padding: 20px; border: 1px solid #ddd; border-radius: 8px; text-decoration: none; color: inherit; display: block;">
                <h3 style="color: #0056b3; margin-top: 0;">🤝 CSE Meeting Guide</h3>
                <p>What to expect at your Annual Review or Initial Eligibility meeting.</p>
            </a>

            <a href="./evaluation-process.html" class="hub-card" style="padding: 20px; border: 1px solid #ddd; border-radius: 8px; text-decoration: none; color: inherit; display: block;">
                <h3 style="color: #0056b3; margin-top: 0;">📝 Request Evaluation</h3>
                <p>How to trigger the 60-day timeline for testing.</p>
            </a>

            <a href="./discipline-rights.html" class="hub-card" style="padding: 20px; border: 1px solid #ddd; border-radius: 8px; text-decoration: none; color: inherit; display: block;">
                <h3 style="color: #0056b3; margin-top: 0;">⚖️ Discipline & Rights</h3>
                <p>Suspensions, Manifestation Determination, and Due Process.</p>
            </a>

        </div>

        <section class="district-faq">
            <h2>Common Questions in {district_name}</h2>
            {faq_html}
        </section>
      </main>
      {footer}
    </body>
    </html>"""

    # Write the Hub Page
    with open(f"{output_path}/index.html", "w", encoding="utf-8") as f:
        f.write(HUB_TEMPLATE.format(
            district_name=district_name,
            leader_title=contact_data['leader'],
            authority_summary=ai_data['authority_summary'],
            faq_html=ai_data['faq_html'],
            schema_json=ai_data['schema_json'],
            css_links=CSS_LINKS, navbar=NAVBAR_HTML, footer=FOOTER_HTML
        ))
    
    time.sleep(1)

# EXECUTION
if __name__ == "__main__":
    setup_directories()
    for i, row in nyc_df.iterrows():
        generate_district_ecosystem(row, type="NYC")
    for i, row in state_df.iterrows():
        generate_district_ecosystem(row, type="STATE")
    print("✅ DONE! Full Site Ecosystem Generated.")