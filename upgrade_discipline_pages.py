import os
from bs4 import BeautifulSoup

def get_lawyer_sidebar(district_name):
    # Responsive, inline-styled Lawyer Card wired to the Google Sheet script
    return f"""
    <div class="premium-sidebar-right" style="flex: 1 1 30%; min-width: 300px; position: sticky; top: 20px;">
        <div style="background: #fdfaf5; border: 1px solid #d6cbbf; border-radius: 6px; overflow: hidden; font-family: 'DM Sans', sans-serif; box-shadow: 0 10px 25px rgba(0,0,0,0.08);">
           
           <div style="background: #1a1410; padding: 24px 24px 20px; position: relative;">
              <p style="font-size: 9px; font-weight: 600; letter-spacing: 0.25em; text-transform: uppercase; color: #b8963a; margin-bottom: 8px; margin-top: 0;">Special Education Law</p>
              <h3 style="font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 400; color: #f5f0e8; line-height: 1.1; margin: 0;">Need a <em>{district_name}</em> Lawyer?</h3>
              <div style="height: 2px; background: linear-gradient(90deg, transparent, #b8963a, transparent); margin-top: 20px; width: 100%;"></div>
           </div>

           <div style="padding: 24px; background: #faf7f2;" id="lawyerFormContainer">
              <p style="font-family: 'Cormorant Garamond', serif; font-size: 19px; font-weight: 600; color: #1a1410; line-height: 1.3; margin-top: 0; margin-bottom: 8px;">
                 You shouldn't have to figure this out alone.
              </p>
              <p style="font-size: 13px; line-height: 1.5; color: #6b5f53; margin-bottom: 20px;">
                 A free 15-minute call can help you understand your legal options before an MDR or discipline hearing.
              </p>

              <form id="disciplineLeadForm" style="display: flex; flex-direction: column; gap: 14px;">
                 
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
                         <option>My child was suspended or removed</option>
                         <option>We are facing an MDR or alternative placement</option>
                         <option>I need to file a formal state complaint</option>
                         <option>The school is ignoring the IEP</option>
                         <option>Something else</option>
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
            const form = document.getElementById('disciplineLeadForm');
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

def main():
    print("Scanning for discipline-rights.html files...")

    files_to_process = []
    for root, dirs, files in os.walk('.'):
        parts = root.split(os.sep)
        if 'districts' in parts and parts[-1] != 'districts':
            if 'discipline-rights.html' in files:
                files_to_process.append(os.path.join(root, 'discipline-rights.html'))
                
    if not files_to_process:
        print("ERROR: Could not find any district discipline-rights.html files.")
        return

    count = 0
    for file_path in files_to_process:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Clean out old sidebar if one was previously injected
        existing_sidebar = soup.find('div', class_='premium-sidebar-right')
        if existing_sidebar:
            existing_sidebar.decompose()
            
        # Locate the content container
        content_div = soup.find('div', class_='content-body')
        if not content_div:
            content_div = soup.find('section', class_='local-aeo-section')
            
        if not content_div:
            print(f"[SKIPPED] {file_path} - No valid content container found.")
            continue

        # Extract the district name dynamically
        title_tag = soup.find('title')
        district_name = "New York"
        if title_tag:
            title_text = title_tag.text.strip()
            # Most titles look like "Discipline Rights in Albany City SD | ..."
            if ' in ' in title_text and '|' in title_text:
                district_name = title_text.split(' in ')[1].split('|')[0].strip()
            elif '|' in title_text:
                district_name = title_text.split('|')[0].strip()
                    
        # Check if it's already inside a flex container from a previous pass
        split_container = soup.find('div', class_='premium-split-container')
        
        if split_container:
            # Inject new Lawyer sidebar
            right_col_soup = BeautifulSoup(get_lawyer_sidebar(district_name), 'html.parser')
            split_container.append(right_col_soup)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            count += 1
            print(f"[SUCCESS] Injected Lawyer Sidebar into existing layout: {file_path}")
            
        else:
            # Build the 70/30 layout from scratch
            split_section = soup.new_tag('div', **{'class': 'premium-split-container', 'style': 'display: flex; flex-wrap: wrap; gap: 40px; align-items: flex-start; width: 100%; margin-top: 30px;'})
            
            # Left column gets the old class so styling is preserved
            old_class = content_div.get('class', [''])[0]
            left_col = soup.new_tag('div', **{'class': old_class, 'style': 'flex: 1 1 60%; min-width: 300px; max-width: 100%; padding: 0; margin-top: 0;'})
            for child in list(content_div.contents):
                left_col.append(child.extract())
                
            # Right column (The Lawyer Card)
            right_col_soup = BeautifulSoup(get_lawyer_sidebar(district_name), 'html.parser')
            
            # Assemble and swap
            split_section.append(left_col)
            split_section.append(right_col_soup)
            content_div.replace_with(split_section)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            count += 1
            print(f"[SUCCESS] Built layout and injected Lawyer Sidebar: {file_path}")

    print(f"\n======================================")
    print(f"DONE! Upgraded {count} discipline pages.")
    print(f"======================================")

if __name__ == '__main__':
    main()