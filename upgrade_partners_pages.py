import os
from bs4 import BeautifulSoup

def get_subnav_css():
    return """
<style id="district-subnav-css">
/* district-subnav styling */
.district-subnav {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  margin: 0 0 24px 0;
}
.district-subnav a {
  display: inline-block;
  padding: 5px 11px;
  border-radius: 4px;
  font-size: 0.82rem;
  font-weight: 600;
  text-decoration: none;
  color: #0056b3;
  background: #fff;
  border: 1px solid #cbd5e1;
  white-space: nowrap;
  transition: background 0.15s;
}
.district-subnav a:hover { background: #dbeafe; }
.district-subnav a.subnav-active {
  background: #002868;
  color: #fff;
  border-color: #002868;
  cursor: default;
}
</style>
"""

def get_subnav_html(district_slug, district_name):
    return f"""
    <div class="aeo-authority-block" style="margin-bottom: 15px;">
        <a href="/districts/{district_slug}/" style="color: #0056b3; font-weight: 600; text-decoration: none;">
         ← Back to {district_name} Hub
        </a>
    </div>
    <nav aria-label="Pages in this district" class="district-subnav">
        <a href="/districts/{district_slug}/">🏠 Hub</a>
        <a href="/districts/{district_slug}/leadership-directory.html">📞 Contacts</a>
        <a href="/districts/{district_slug}/cse-meeting-guide.html">🤝 CSE Guide</a>
        <a href="/districts/{district_slug}/evaluation-process.html">📝 Evaluations</a>
        <a href="/districts/{district_slug}/discipline-rights.html">⚖️ Discipline</a>
        <a aria-current="page" class="subnav-active" href="/districts/{district_slug}/partners.html">🤲 Partners</a>
        <a href="/districts/{district_slug}/special-ed-updates.html">📰 Updates</a>
    </nav>
    """

def get_large_law_card(district_name):
    return f"""
    <style>
    .large-law-card {{
        display: flex;
        flex-wrap: wrap;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.15);
        margin: 40px 0 60px 0;
        border: 1px solid #d6cbbf;
    }}
    .ll-left {{
        flex: 1 1 45%;
        background: #1a1410;
        padding: 50px 45px;
        color: #f5f0e8;
        position: relative;
    }}
    .ll-right {{
        flex: 1 1 55%;
        background: #faf7f2;
        padding: 50px 45px;
    }}
    .ll-eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.25em; text-transform: uppercase; color: #b8963a; margin-bottom: 15px; font-family: 'DM Sans', sans-serif;}}
    .ll-title {{ font-family: 'Cormorant Garamond', serif; font-size: 42px; font-weight: 400; color: #f5f0e8; line-height: 1.1; margin: 0 0 20px 0; }}
    .ll-title em {{ color: #b8963a; font-style: italic; }}
    .ll-desc {{ font-family: 'DM Sans', sans-serif; font-size: 16px; line-height: 1.6; color: #d6cbbf; margin-bottom: 35px; font-weight: 300;}}
    .ll-list {{ list-style: none; padding: 0; margin: 0; font-family: 'DM Sans', sans-serif; }}
    .ll-list li {{ font-size: 15px; color: #f5f0e8; padding: 10px 0 10px 26px; position: relative; border-bottom: 1px solid rgba(214, 203, 191, 0.1); }}
    .ll-list li:last-child {{ border-bottom: none; }}
    .ll-list li::before {{ content: '§'; font-family: 'Cormorant Garamond', serif; font-size: 18px; color: #b8963a; position: absolute; left: 0; top: 8px; }}
    
    .ll-form-title {{ font-family: 'Cormorant Garamond', serif; font-size: 28px; font-weight: 600; color: #1a1410; margin: 0 0 8px 0; }}
    .ll-form-desc {{ font-family: 'DM Sans', sans-serif; font-size: 15px; color: #6b5f53; margin-bottom: 25px; line-height: 1.5; }}
    .ll-form {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-family: 'DM Sans', sans-serif; }}
    .ll-full {{ grid-column: 1 / -1; }}
    .ll-label {{ display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #6b5f53; margin-bottom: 6px; }}
    .ll-input {{ width: 100%; padding: 14px; border: 1px solid #d6cbbf; font-size: 14px; color: #1a1410; background: #fff; border-radius: 4px; outline: none; box-sizing: border-box; }}
    .ll-select {{ -webkit-appearance: none; background-image: url('data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2210%22%20height%3D%226%22%3E%3Cpath%20d%3D%22M0%200l5%206%205-6z%22%20fill%3D%22%23b8963a%22%2F%3E%3C%2Fsvg%3E'); background-repeat: no-repeat; background-position: right 14px center; cursor: pointer; }}
    .ll-btn {{ width: 100%; background: #1a1410; color: #b8963a; border: none; padding: 18px; font-size: 13px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; border-radius: 4px; transition: all 0.25s ease; grid-column: 1 / -1; margin-top: 10px;}}
    .ll-btn:hover {{ background: #b8963a; color: #1a1410; }}
    
    @media (max-width: 768px) {{
        .ll-left, .ll-right {{ flex: 1 1 100%; padding: 35px 25px; }}
        .ll-form {{ grid-template-columns: 1fr; }}
        .ll-full {{ grid-column: 1; }}
        .ll-btn {{ grid-column: 1; }}
    }}
    </style>

    <div class="large-law-card" id="largeLawFirmCard">
        <div class="ll-left">
            <p class="ll-eyebrow">Local Representation</p>
            <h2 class="ll-title">Need a <em>{district_name}</em> Advocate?</h2>
            <p class="ll-desc">
                Don't walk into your CSE meeting unprepared. The district's representatives are legally trained professionals — but you have equal rights at the table.
            </p>
            <ul class="ll-list">
                <li>CSE / IEP Meeting Advocacy</li>
                <li>60-Day Evaluation Enforcement</li>
                <li>Independent Educational Evaluations (IEE)</li>
                <li>Discipline, Manifestation (MDR) & Suspensions</li>
                <li>Due Process Hearings & State Complaints</li>
            </ul>
        </div>

        <div class="ll-right" id="partnerFormContainer">
            <h3 class="ll-form-title">Request a Case Evaluation</h3>
            <p class="ll-form-desc">Get connected with a specialized education advocate. No fees unless we take your case.</p>
            
            <form id="partnerLeadForm" class="ll-form">
                <div>
                    <label class="ll-label">Parent Name</label>
                    <input type="text" id="pName" class="ll-input" placeholder="First and last name" required />
                </div>
                <div>
                    <label class="ll-label">Phone Number</label>
                    <input type="tel" id="pPhone" class="ll-input" placeholder="(555) 000-0000" required />
                </div>
                <div class="ll-full">
                    <label class="ll-label">Email Address</label>
                    <input type="email" id="pEmail" class="ll-input" placeholder="Your best email address" required />
                </div>
                <div class="ll-full">
                    <label class="ll-label">Primary Concern</label>
                    <select id="pIssue" class="ll-input ll-select" required>
                        <option value="" disabled selected>Select the main issue...</option>
                        <option>Upcoming CSE / IEP Meeting</option>
                        <option>Evaluation Denied or Delayed</option>
                        <option>School Discipline / Suspension</option>
                        <option>IEP Not Being Followed</option>
                        <option>Due Process Filing</option>
                        <option>Other</option>
                    </select>
                </div>
                <button type="submit" id="pSubmitBtn" class="ll-btn">
                    Secure My Free Consultation
                </button>
            </form>
            <div style="font-size: 11px; color: #a09488; line-height: 1.6; margin-top: 16px; text-align: center; font-family: 'DM Sans', sans-serif;">
                <strong><i class="fas fa-lock"></i> 100% Confidential.</strong> No obligation.
            </div>
        </div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const form = document.getElementById('partnerLeadForm');
            const submitBtn = document.getElementById('pSubmitBtn');
            const container = document.getElementById('partnerFormContainer');

            if (form && submitBtn) {{
                form.addEventListener('submit', function(e) {{
                    e.preventDefault();
                    
                    submitBtn.innerHTML = 'Securely Sending...';
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.7';

                    const formData = new URLSearchParams();
                    formData.append('name', document.getElementById('pName').value || 'Not provided');
                    formData.append('email', document.getElementById('pEmail').value || 'Not provided');
                    formData.append('phone', document.getElementById('pPhone').value || 'Not provided');
                    formData.append('concern', document.getElementById('pIssue').value || 'Not provided');
                    formData.append('pageUrl', window.location.href);

                    const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwWpGXg3JMJnxyzUlJHPlQRnE_R2Dh6oFvapMureXQWG_0bLOBtN_e7f5s5jnKRdcG-/exec';

                    fetch(GOOGLE_SCRIPT_URL, {{
                        method: 'POST',
                        body: formData,
                        mode: 'no-cors'
                    }})
                    .then(() => {{
                        container.innerHTML = `
                            <div style="text-align: center; padding: 60px 20px;">
                                <div style="color: #b8963a; font-size: 56px; margin-bottom: 20px;">✓</div>
                                <h4 style="font-family: 'Cormorant Garamond', serif; font-size: 32px; color: #1a1410; margin-bottom: 12px; font-weight: 600;">Request Received</h4>
                                <p style="font-size: 16px; color: #6b5f53; line-height: 1.6; font-family: 'DM Sans', sans-serif;">
                                    Your information has been securely routed. A legal professional familiar with your district will reach out to you shortly.
                                </p>
                            </div>
                        `;
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                        submitBtn.innerHTML = 'Error. Please Try Again.';
                        submitBtn.disabled = false;
                        submitBtn.style.opacity = '1';
                    }});
                }});
            }}
        }});
        </script>
    </div>
    """

def main():
    print("Scanning for partners.html files in district folders...")

    files_to_process = []
    for root, dirs, files in os.walk('.'):
        parts = root.split(os.sep)
        if 'districts' in parts and parts[-1] != 'districts':
            if 'partners.html' in files:
                files_to_process.append(os.path.join(root, 'partners.html'))
                
    if not files_to_process:
        print("ERROR: Could not find any district partners.html files.")
        return

    count = 0
    for file_path in files_to_process:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # --- 1. CLEAN UP HTML BUGS (Double Headers/Footers) ---
        headers = soup.find_all('header', class_='site-header')
        if len(headers) > 0 and headers[0].find('header'):
            headers[0].unwrap() # Removes the outer wrapper, leaving the inner intact

        footers = soup.find_all('footer', class_='site-footer')
        if len(footers) > 0 and footers[0].find('footer'):
            footers[0].unwrap()

        # --- 2. EXTRACT DISTRICT INFO ---
        district_slug = file_path.split(os.sep)[-2]
        
        title_tag = soup.find('title')
        district_name = "New York State"
        if title_tag and ' in ' in title_tag.text:
            district_name = title_tag.text.split(' in ')[1].split('|')[0].strip()

        # --- 3. INJECT SUBNAV CSS ---
        head = soup.find('head')
        if head and not soup.find(id='district-subnav-css'):
            head.append(BeautifulSoup(get_subnav_css(), 'html.parser'))

        # --- 4. SWAP THE OLD SILO NAV FOR THE NEW HUB NAV ---
        old_nav = soup.find('nav', class_='silo-nav')
        if old_nav:
            new_nav_soup = BeautifulSoup(get_subnav_html(district_slug, district_name), 'html.parser')
            old_nav.replace_with(new_nav_soup)

        # --- 5. SWAP THE OLD FEATURED AD ZONE WITH THE LARGE LAW BOX ---
        ad_zone = soup.find('div', class_='featured-ad-zone')
        if ad_zone:
            large_card_soup = BeautifulSoup(get_large_law_card(district_name), 'html.parser')
            ad_zone.replace_with(large_card_soup)
        else:
            # If it was already replaced, check if we need to update it
            existing_card = soup.find('div', id='largeLawFirmCard')
            if not existing_card:
                # Find a good place to inject it (after the divider)
                divider = soup.find('hr', class_='divider')
                if divider:
                    large_card_soup = BeautifulSoup(get_large_law_card(district_name), 'html.parser')
                    divider.insert_after(large_card_soup)

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        count += 1
        print(f"[SUCCESS] Fixed header bugs, added Hub Nav, injected Large Law Card: {file_path}")

    print(f"\n======================================")
    print(f"DONE! Upgraded {count} Partners pages.")
    print(f"======================================")

if __name__ == '__main__':
    main()