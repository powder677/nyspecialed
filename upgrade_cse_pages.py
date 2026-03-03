import os
import re
from bs4 import BeautifulSoup

def parse_dense_content(raw_html):
    # Fix broken placeholder links from AI generation
    raw_html = raw_html.replace('(LINK TO EVALUATION PAGE)', 'evaluation-process.html')
    raw_html = raw_html.replace('(LINK TO CSE MEETING PAGE)', 'cse-meeting-guide.html')
    raw_html = raw_html.replace('(LINK TO IEP PAGE)', '../guides/cse-meeting-guide/')
    raw_html = raw_html.replace('(LINK TO DISPUTE RESOLUTION PAGE)', '../guides/dispute-resolution-ny/')
    raw_html = raw_html.replace('(LINK TO PARENT RIGHTS PAGE)', '../guides/')
    raw_html = raw_html.replace('(LINK TO RESOURCES PAGE)', '../resources/')

    # Convert Markdown Links: [Text](URL)
    raw_html = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)', 
        r'<a href="\2" style="color: #0056b3; font-weight: 600; text-decoration: none; border-bottom: 1px solid #0056b3;">\1</a>', 
        raw_html
    )

    # Convert Markdown Bold: **text**
    raw_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', raw_html)
    
    # Split text blocks
    blocks = re.split(r'\n\s*\n', raw_html)
    
    parsed_blocks = []
    in_list = False
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        if block.startswith('<h') or block.startswith('<div') or block.startswith('<section') or block.startswith('<p'):
            if in_list:
                parsed_blocks.append('</ul>')
                in_list = False
            
            # Premium H2 Styling
            if block.startswith('<h2>'):
                block = block.replace('<h2>', '<h2 style="color: #002868; font-size: 2rem; margin-top: 50px; margin-bottom: 20px; border-bottom: 2px solid #d4af37; padding-bottom: 10px; font-family: \'Cormorant Garamond\', serif;">')
            
            parsed_blocks.append(block)
            continue
            
        if block.startswith('* ') or block.startswith('- '):
            if not in_list:
                parsed_blocks.append('<ul style="margin-top: 15px; margin-bottom: 30px; padding-left: 25px; line-height: 1.8; color: #334155; font-size: 1.1rem;">')
                in_list = True
            
            list_items = block.split('\n')
            for item in list_items:
                item = item.strip()
                if item.startswith('* ') or item.startswith('- '):
                    parsed_blocks.append(f'<li style="margin-bottom: 12px; padding-left: 8px;">{item[2:].strip()}</li>')
                elif item:
                    parsed_blocks.append(f'{item}') 
            continue
            
        if in_list:
            parsed_blocks.append('</ul>')
            in_list = False
            
        # Standard paragraph wrapping
        parsed_blocks.append(f'<p style="margin-bottom: 28px; line-height: 1.85; color: #334155; font-size: 1.125rem;">{block}</p>')
            
    if in_list:
        parsed_blocks.append('</ul>')
        
    return '\n'.join(parsed_blocks)

def get_law_firm_sidebar(district_name):
    # This HTML is adapted directly from your law.html upload
    return f"""
    <div class="premium-sidebar-right">
        <div class="premium-card" style="background: #ffffff; border: 1px solid #d6cbbf; border-radius: 6px; box-shadow: 0 15px 35px rgba(0,0,0,0.08); overflow: hidden;">
           
           <div class="card-header" style="background: #1a1410; padding: 28px 24px 24px; position: relative;">
              <p style="font-size: 9px; font-weight: 600; letter-spacing: 0.3em; text-transform: uppercase; color: #d4ad5a; margin-bottom: 10px; font-family: 'DM Sans', sans-serif;">Special Education Law</p>
              <h3 style="font-family: 'Cormorant Garamond', serif; font-size: 28px; font-weight: 400; color: #f5f0e8; line-height: 1.1; margin: 0;">Need a <em>{district_name}</em> Advocate?</h3>
              <div style="height: 2px; background: linear-gradient(90deg, transparent, #b8963a, transparent); margin-top: 20px; width: 100%;"></div>
           </div>
           
           <div class="card-body" style="padding: 24px; background: #faf7f2;">
              <p style="font-family: 'Cormorant Garamond', serif; font-size: 19px; font-weight: 600; color: #1a1410; line-height: 1.35; margin-bottom: 15px;">
                 Don't walk into your CSE meeting unprepared.
              </p>
              
              <p style="font-size: 13.5px; line-height: 1.6; color: #3d3028; margin-bottom: 25px; font-family: 'DM Sans', sans-serif;">
                 The school's representatives are legally trained — but you have equal rights. Request a free case evaluation today.
              </p>
              
              <form action="#" method="POST" style="display: flex; flex-direction: column; gap: 16px; font-family: 'DM Sans', sans-serif;">
                 
                 <div>
                     <label style="display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: #6b5f53; margin-bottom: 6px;">Parent Name</label>
                     <input type="text" placeholder="Full name" required style="width: 100%; padding: 12px; border: 1px solid #d6cbbf; font-size: 13px; outline: none; background: #fff; box-sizing: border-box;" />
                 </div>
                 
                 <div>
                     <label style="display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: #6b5f53; margin-bottom: 6px;">Phone Number</label>
                     <input type="tel" placeholder="(555) 000-0000" required style="width: 100%; padding: 12px; border: 1px solid #d6cbbf; font-size: 13px; outline: none; background: #fff; box-sizing: border-box;" />
                 </div>
                 
                 <div>
                     <label style="display: block; font-size: 10px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: #6b5f53; margin-bottom: 6px;">Primary Concern</label>
                     <select required style="width: 100%; padding: 12px; border: 1px solid #d6cbbf; font-size: 13px; outline: none; background-color: #fff; cursor: pointer; box-sizing: border-box; -webkit-appearance: none; background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23b8963a%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E'); background-repeat: no-repeat; background-position: right 12px center; background-size: 10px;">
                         <option value="" disabled selected>Select...</option>
                         <option>IEP / Annual Review Meeting</option>
                         <option>Evaluation Denied</option>
                         <option>School Discipline / Suspension</option>
                         <option>Private Placement Dispute</option>
                         <option>Due Process Filing</option>
                         <option>Other</option>
                     </select>
                 </div>
                 
                 <button type="submit" style="width: 100%; background: #1a1410; color: #d4ad5a; border: none; padding: 16px; font-size: 11px; font-weight: 600; letter-spacing: 0.2em; text-transform: uppercase; cursor: pointer; margin-top: 10px; transition: background 0.2s;">
                    Request Consultation
                 </button>
              </form>
              
              <div style="font-size: 11px; color: #a09488; line-height: 1.6; margin-top: 20px; padding-top: 20px; border-top: 1px solid #d6cbbf; text-align: center; font-family: 'DM Sans', sans-serif;">
                 <strong><i class="fas fa-lock"></i> Confidential Inquiry.</strong><br>No obligation, no fees unless we take your case.
              </div>
           </div>
        </div>
    </div>
    """

def main():
    print("Scanning for cse-meeting-guide.html files in district folders...")

    files_to_process = []
    for root, dirs, files in os.walk('.'):
        parts = root.split(os.sep)
        if 'districts' in parts and parts[-1] != 'districts':
            if 'cse-meeting-guide.html' in files:
                files_to_process.append(os.path.join(root, 'cse-meeting-guide.html'))
                
    if not files_to_process:
        print("ERROR: Could not find any district cse-meeting-guide.html files.")
        return

    count = 0
    for file_path in files_to_process:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if already upgraded
        if soup.find('div', class_='premium-sidebar-right'):
            print(f"[SKIPPED] {file_path} - Already upgraded.")
            continue
            
        # Find the main content container
        section = soup.find('section', class_='local-aeo-section')
        if not section:
            print(f"[SKIPPED] {file_path} - Needs manual check (no local-aeo-section found).")
            continue
            
        # Extract the district name dynamically from the page
        title_tag = soup.find('title')
        district_name = "New York"
        if title_tag:
            title_text = title_tag.text.strip()
            if 'CSE Meeting' in title_text:
                district_name = title_text.split('CSE Meeting')[0].strip()
            elif '|' in title_text:
                district_name = title_text.split('|')[0].strip()
                
        # Detach from the old CSS rules
        section['class'] = 'premium-split-section'
        
        # Build the new layout containers
        container = soup.new_tag('div', **{'class': 'premium-split-container'})
        left_col = soup.new_tag('div', **{'class': 'premium-content-left'})
        
        # Format and move the dense text into the left column
        inner_html = section.decode_contents()
        parsed_html = parse_dense_content(inner_html)
        
        section.clear()
        
        new_soup = BeautifulSoup(parsed_html, 'html.parser')
        left_col.append(new_soup)
            
        # Generate the Law Firm Advocate Sidebar HTML
        right_col_soup = BeautifulSoup(get_law_firm_sidebar(district_name), 'html.parser')
        
        # Append columns to the container, and container to the section
        container.append(left_col)
        container.append(right_col_soup)
        section.append(container)
            
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        count += 1
        print(f"[SUCCESS] Upgraded layout & text for: {file_path}")

    print(f"\nDONE! Upgraded {count} pages.")

if __name__ == '__main__':
    main()