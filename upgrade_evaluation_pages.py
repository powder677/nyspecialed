import os
from bs4 import BeautifulSoup

def get_lawyer_sidebar(district_name):
    # Responsive, inline-styled Lawyer Card wired to the Google Sheet script
    return f"""
    <div class="premium-sidebar-right" style="flex: 1 1 30%; min-width: 300px; position: sticky; top: 20px;">
        <div style="background: #fdfaf5; border: 1px solid #d6cbbf; border-radius: 6px; overflow: hidden; font-family: 'DM Sans', sans-serif; box-shadow: 0 10px 25px rgba(0,0,0,0.08);">
           
           <div style="background: #1a1410; padding: 24px 24px 20px; position: relative;">
              <p style="font-size: 9px; font-weight: 600; letter-spacing: 0.25em; text-transform: uppercase; color: #b8963a; margin-bottom: 8px; margin-top: 0;">Special Education Law</p>
              <h3 style="font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 400; color: #f5f0e8; line-height: 1.1; margin: 0;">Need a <em>{district_name}</em> Advocate?</h3>
              <div style="height: 2px; background: linear-gradient(90deg, transparent, #b8963a, transparent); margin-top: 20px; width: 100%;"></div>
           </div>

           <div style="padding: 24px; background: #faf7f2;" id="lawyerFormContainer">
              <p style="font-family: 'Cormorant Garamond', serif; font-size: 19px; font-weight: 600; color: #1a1410; line-height: 1.3; margin-top: 0; margin-bottom: 8px;">
                 You shouldn't have to figure this out alone.
              </p>
              <p style="font-size: 13px; line-height: 1.5; color: #6b5f53; margin-bottom: 20px;">
                 A free 15-minute call can help you understand your legal rights if the school denies an evaluation.
              </p>

              <form id="evalLeadForm" style="display: flex; flex-direction: column; gap: 14px;">
                 
                 <div>
                     <label style="display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #6b5f53; margin-bottom: 5px;">Your Name</label>
                     <input type="text" id="leadName" placeholder="First and last name" required style="width: 100%; padding: 12px; border: 1px solid #d6cbbf; font-size: 13px; color: #1a1410; background: #fff; outline: none; box-sizing: border-box; font-family: 'DM Sans', sans-serif; border-radius: 4px;" />
                 </div>

                 <div>
                     <label style="display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #6b5f53; margin-bottom: 5px;">Email Address</label>
                     <input type="email" id="leadEmail" placeholder="Where should we reach you?" required style="width: 100%; padding: 12px; border: 1px solid #d6cbbf; font-size: 13px; color: #1a1410; background: #fff; outline: none; box-sizing: border-box; font-family: 'DM Sans', sans-serif; border-radius: 4px;" />
                 </div>
                 
                 <div>
                     <label style="display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #6b5f53; margin-bottom: 5px;">Phone <span style="text-transform: lowercase; font-weight: 400;">(optional)</span></label>
                     <input type="tel" id="leadPhone" placeholder="(555) 000-0000" style="width: 100%; padding: 12px; border: 1px solid #d6cbbf; font-size: 13px; color: #1a1410; background: #fff; outline: none; box-sizing: border-box; font-family: 'DM Sans', sans-serif; border-radius: 4px;" />
                 </div>
                 
                 <div>
                     <label style="display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #6b5f53; margin-bottom: 5px;">What's going on?</label>
                     <select id="leadIssue" required style="width: 100%; padding: 12px; border: 1px solid #d6cbbf; font-size: 13px; color: #1a1410; background-color: #fff; cursor: pointer; box-sizing: border-box; font-family: 'DM Sans', sans-serif; border-radius: 4px; -webkit-appearance: none; background-image: url('data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2210%22%20height%3D%226%22%3E%3Cpath%20d%3D%22M0%200l5%206%205-6z%22%20fill%3D%22%23b8963a%22%2F%3E%3C%2Fsvg%3E'); background-repeat: no-repeat; background-position: right 12px center;">
                         <option value="" disabled selected>Choose what fits best...</option>
                         <option>School is refusing to evaluate</option>
                         <option>I want an Independent Evaluation (IEE)</option>
                         <option>CSE / IEP Meeting</option>
                         <option>School Discipline / Suspension</option>
                         <option>Due Process Filing</option>
                         <option>Other</option>
                     </select>
                 </div>
                 
                 <button type="submit" id="leadSubmitBtn" onmouseover="this.style.background='#b8963a'; this.style.color='#1a1410';" onmouseout="this.style.background='#1a1410'; this.style.color='#b8963a';" style="width: 100%; background: #1a1410; color: #b8963a; border: none; padding: 14px; font-size: 11px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; margin-top: 8px; border-radius: 4px; transition: all 0.25s ease; box-sizing: border-box; font-family: 'DM Sans', sans-serif;">
                    Get My Free 15-Minute Call
                 </button>
              </form>
              
              <div style="font-size: 11px; color: #9a8f86; line-height: 1.6; margin-top: 14px; text-align: center; display: flex; align-items: center; justify-content: center; gap: 6px;">
                 <svg fill="none" height="13" stroke="#b8963a" stroke-width="2.5" viewBox="0 0 24 24" width="13"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                 Confidential. No spam. No pressure.
              </div>
           </div>
           
           <div style="background: #f0ebe3; padding: 12px 24px; text-align: center; font-size: 10px; color: #9a8f86; border-top: 1px solid #d6cbbf;">
              Attorney Advertising · Results may vary.
           </div>
        </div>

        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const form = document.getElementById('evalLeadForm');
            const submitBtn = document.getElementById('leadSubmitBtn');
            const container = document.getElementById('lawyerFormContainer');

            if (form && submitBtn) {{
                form.addEventListener('submit', function(e) {{
                    e.preventDefault();
                    
                    submitBtn.innerHTML = 'Securely Sending...';
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.7';

                    const formData = new URLSearchParams();
                    formData.append('name', document.getElementById('leadName').value || 'Not provided');
                    formData.append('email', document.getElementById('leadEmail').value || 'Not provided');
                    formData.append('phone', document.getElementById('leadPhone').value || 'Not provided');
                    formData.append('concern', document.getElementById('leadIssue').value || 'Not provided');
                    formData.append('pageUrl', window.location.href);

                    const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwWpGXg3JMJnxyzUlJHPlQRnE_R2Dh6oFvapMureXQWG_0bLOBtN_e7f5s5jnKRdcG-/exec';

                    fetch(GOOGLE_SCRIPT_URL, {{
                        method: 'POST',
                        body: formData,
                        mode: 'no-cors'
                    }})
                    .then(() => {{
                        container.innerHTML = `
                            <div style="text-align: center; padding: 40px 10px;">
                                <div style="color: #b8963a; font-size: 48px; margin-bottom: 15px;">✓</div>
                                <h4 style="font-family: 'Cormorant Garamond', serif; font-size: 26px; color: #1a1410; margin-bottom: 10px; font-weight: 600;">Request Received</h4>
                                <p style="font-size: 14px; color: #6b5f53; line-height: 1.6; font-family: 'DM Sans', sans-serif;">
                                    Your information has been securely routed. A legal professional will reach out to you shortly.
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

def get_sales_cards_html():
    return """
    <style>
    /* STACKED OFFERS FOR NEW YORK */
    .offers-container { display: flex; flex-direction: column; gap: 24px; margin-top: 50px; border-top: 2px solid #e2e8f0; padding-top: 40px; }
    .offers-title { font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; color: #002868; text-align: center; margin: 0 0 5px 0; border: none; padding: 0;}
    .offers-subtitle { text-align: center; color: #475569; font-family: 'DM Sans', sans-serif; margin-bottom: 25px; font-size: 1.1rem;}
    
    .sales-card { background: linear-gradient(135deg, #002868 0%, #1e3a8a 100%); padding: 36px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15); position: relative; overflow: hidden; }
    .sales-card .badge { background: #d4af37; color: #002868; padding: 6px 16px; border-radius: 50px; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; display: inline-block; margin-bottom: 15px;}
    .sales-card h3 { margin: 0 0 12px; color: #ffffff; font-size: 1.8rem; font-family: 'Cormorant Garamond', serif; }
    .sales-card p { color: #e2e8f0; margin: 0 auto 24px; font-size: 1.05rem; line-height: 1.6; max-width: 90%; font-family: 'DM Sans', sans-serif;}
    .sales-card a.buy-btn { background: #d4af37; color: #002868; padding: 16px 32px; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 1.1rem; display: inline-block; transition: 0.2s; font-family: 'DM Sans', sans-serif;}
    .sales-card a.buy-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(212,175,55,0.4); }

    /* COMING SOON CARD STYLING */
    .sales-card.coming-soon { background: linear-gradient(135deg, #475569 0%, #334155 100%); }
    .sales-card.coming-soon .badge { background: #94a3b8; color: #1e293b; }
    .sales-card.coming-soon p { color: #cbd5e1; }
    .sales-card.coming-soon a.buy-btn { background: #64748b; color: #f8fafc; cursor: not-allowed; }
    .sales-card.coming-soon a.buy-btn:hover { transform: none; box-shadow: none; }
    
    /* DIAGONAL OVERLAY */
    .coming-soon-overlay {
        position: absolute;
        top: 28px;
        right: -45px;
        background: #d4af37;
        color: #002868;
        padding: 8px 50px;
        font-weight: 800;
        font-size: 0.85rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        transform: rotate(45deg);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        z-index: 2;
        font-family: 'DM Sans', sans-serif;
    }
    </style>
    
    <div class="offers-container" id="premium-offers">
        <h2 class="offers-title">Take the Next Step</h2>
        <p class="offers-subtitle">Protect your child's right to a Free Appropriate Public Education.</p>
        
        <div class="sales-card">
            <span class="badge">Essential</span>
            <h3>The CSE Meeting Prep Kit</h3>
            <p>Master the NY Special Education evaluation and IEP process. Includes independent evaluation (IEE) request templates, 60-day timeline trackers, and exact scripts to use at your meeting.</p>
            <a href="/contact/" class="buy-btn">Get the Prep Kit — $47</a>
        </div>

        <div class="sales-card coming-soon">
            <div class="coming-soon-overlay">Coming Soon</div>
            <span class="badge">Advanced</span>
            <h3>The CSE Kit + Autism Pack</h3>
            <p>Everything in the standard Prep Kit, plus specialized autism IEP goals, sensory diet accommodations, and FBA/BIP behavioral strategies tailored specifically for New York schools.</p>
            <a href="#" class="buy-btn" onclick="return false;">Available Next Month</a>
        </div>
    </div>
    """

def main():
    print("Scanning for evaluation-process.html files...")

    files_to_process = []
    for root, dirs, files in os.walk('.'):
        parts = root.split(os.sep)
        if 'districts' in parts and parts[-1] != 'districts':
            if 'evaluation-process.html' in files:
                files_to_process.append(os.path.join(root, 'evaluation-process.html'))
                
    if not files_to_process:
        print("ERROR: Could not find any district evaluation-process.html files.")
        return

    count = 0
    for file_path in files_to_process:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Clean out old injections to prevent duplicates
        existing_sidebar = soup.find('div', class_='premium-sidebar-right')
        if existing_sidebar:
            existing_sidebar.decompose()
            
        existing_offers = soup.find('div', id='premium-offers')
        if existing_offers:
            existing_offers.decompose()
            
        # 2. Locate the content container
        content_div = soup.find('div', class_='content-body')
        if not content_div:
            content_div = soup.find('section', class_='local-aeo-section')
            
        if not content_div:
            print(f"[SKIPPED] {file_path} - No valid content container found.")
            continue

        # 3. Extract the district name dynamically
        title_tag = soup.find('title')
        district_name = "New York"
        if title_tag:
            title_text = title_tag.text.strip()
            # Title looks like "Requesting an Evaluation in Mount Vernon City SD"
            if ' in ' in title_text:
                district_name = title_text.split(' in ')[1].split('|')[0].strip()
            elif '|' in title_text:
                district_name = title_text.split('|')[0].strip()
                    
        # 4. Handle Layout and Injections
        split_container = soup.find('div', class_='premium-split-container')
        
        if split_container:
            # We already have the 70/30 wrapper. Just inject the components.
            left_col = split_container.find('div', class_='premium-content-left') or split_container.find('div', class_='content-body')
            
            if left_col:
                sales_soup = BeautifulSoup(get_sales_cards_html(), 'html.parser')
                left_col.append(sales_soup)
                
            right_col_soup = BeautifulSoup(get_lawyer_sidebar(district_name), 'html.parser')
            split_container.append(right_col_soup)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            count += 1
            print(f"[SUCCESS] Injected Offers & Lawyer Sidebar into existing layout: {file_path}")
            
        else:
            # We need to build the 70/30 layout from scratch
            split_section = soup.new_tag('div', **{'class': 'premium-split-container', 'style': 'display: flex; flex-wrap: wrap; gap: 40px; align-items: flex-start; width: 100%; margin-top: 30px;'})
            
            # Left column gets the old class so your existing typography styling is preserved
            old_class = content_div.get('class', [''])[0]
            left_col = soup.new_tag('div', **{'class': old_class, 'style': 'flex: 1 1 60%; min-width: 300px; max-width: 100%; padding: 0; margin-top: 0;'})
            for child in list(content_div.contents):
                left_col.append(child.extract())
                
            # Append Sales cards to bottom of left column
            sales_soup = BeautifulSoup(get_sales_cards_html(), 'html.parser')
            left_col.append(sales_soup)
                
            # Right column (The Lawyer Card)
            right_col_soup = BeautifulSoup(get_lawyer_sidebar(district_name), 'html.parser')
            
            # Assemble and swap
            split_section.append(left_col)
            split_section.append(right_col_soup)
            content_div.replace_with(split_section)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            count += 1
            print(f"[SUCCESS] Built layout, injected Sales Cards & Lawyer Sidebar: {file_path}")

    print(f"\n======================================")
    print(f"DONE! Upgraded {count} Evaluation pages.")
    print(f"======================================")

if __name__ == '__main__':
    main()