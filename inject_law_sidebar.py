import os
from bs4 import BeautifulSoup

def get_mini_law_card(district_name):
    # This is a scaled-down, responsive version of law.html specifically for the 30% sidebar
    return f"""
    <div class="premium-sidebar-right" style="flex: 1 1 30%; min-width: 300px; position: sticky; top: 20px;">
        <div style="background: #fdfaf5; border: 1px solid #d6cbbf; border-radius: 0; overflow: hidden; font-family: 'DM Sans', sans-serif; box-shadow: 0 10px 25px rgba(0,0,0,0.08);">
           
           <div style="background: #1a1410; padding: 24px 28px 20px; position: relative;">
              <p style="font-size: 8px; font-weight: 500; letter-spacing: 0.3em; text-transform: uppercase; color: #b8963a; margin-bottom: 10px; margin-top: 0;">Special Education Law</p>
              <h3 style="font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 400; color: #f5f0e8; line-height: 1.1; margin: 0;">Need a <em>{district_name}</em> Advocate?</h3>
              <div style="height: 2px; background: linear-gradient(90deg, transparent, #b8963a, transparent); margin-top: 20px; width: 100%;"></div>
           </div>

           <div style="padding: 28px; background: #faf7f2;">
              <p style="font-family: 'Cormorant Garamond', serif; font-size: 18px; font-weight: 600; color: #1a1410; line-height: 1.3; margin-top: 0; margin-bottom: 8px;">
                 Don't walk into your CSE meeting unprepared.
              </p>
              <p style="font-size: 12.5px; line-height: 1.6; color: #6b5f53; margin-bottom: 24px; font-weight: 300;">
                 The school's representatives are legally trained — but you have equal rights. Request a free case evaluation.
              </p>

              <form action="#" method="POST" style="display: flex; flex-direction: column; gap: 14px;">
                 
                 <div>
                     <label style="display: block; font-size: 9px; font-weight: 500; letter-spacing: 0.15em; text-transform: uppercase; color: #6b5f53; margin-bottom: 5px;">Parent Name</label>
                     <input type="text" placeholder="Full name" required style="width: 100%; padding: 10px 12px; border: 1px solid #d6cbbf; font-size: 13px; color: #1a1410; background: #fdfaf5; outline: none; box-sizing: border-box; font-family: 'DM Sans', sans-serif;" />
                 </div>
                 
                 <div>
                     <label style="display: block; font-size: 9px; font-weight: 500; letter-spacing: 0.15em; text-transform: uppercase; color: #6b5f53; margin-bottom: 5px;">Phone Number</label>
                     <input type="tel" placeholder="(555) 000-0000" required style="width: 100%; padding: 10px 12px; border: 1px solid #d6cbbf; font-size: 13px; color: #1a1410; background: #fdfaf5; outline: none; box-sizing: border-box; font-family: 'DM Sans', sans-serif;" />
                 </div>
                 
                 <div>
                     <label style="display: block; font-size: 9px; font-weight: 500; letter-spacing: 0.15em; text-transform: uppercase; color: #6b5f53; margin-bottom: 5px;">Primary Concern</label>
                     <select required style="width: 100%; padding: 10px 12px; border: 1px solid #d6cbbf; font-size: 13px; color: #1a1410; background-color: #fdfaf5; cursor: pointer; box-sizing: border-box; font-family: 'DM Sans', sans-serif; -webkit-appearance: none; background-image: url('data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2210%22%20height%3D%226%22%3E%3Cpath%20d%3D%22M0%200l5%206%205-6z%22%20fill%3D%22%23b8963a%22%2F%3E%3C%2Fsvg%3E'); background-repeat: no-repeat; background-position: right 12px center;">
                         <option value="" disabled selected>Select...</option>
                         <option>CSE / IEP Meeting</option>
                         <option>Evaluation Denied</option>
                         <option>504 Plan</option>
                         <option>School Discipline / Suspension</option>
                         <option>Due Process Filing</option>
                         <option>Other</option>
                     </select>
                 </div>
                 
                 <button type="submit" onmouseover="this.style.background='#b8963a'; this.style.color='#1a1410';" onmouseout="this.style.background='#1a1410'; this.style.color='#b8963a';" style="width: 100%; background: #1a1410; color: #b8963a; border: none; padding: 14px 20px; font-size: 11px; font-weight: 500; letter-spacing: 0.22em; text-transform: uppercase; cursor: pointer; margin-top: 8px; transition: all 0.25s ease; box-sizing: border-box; font-family: 'DM Sans', sans-serif;">
                    Request Consultation
                 </button>
              </form>
              
              <div style="font-size: 10px; color: #a09488; line-height: 1.6; margin-top: 16px; padding-top: 16px; border-top: 1px solid #d6cbbf; text-align: center;">
                 <strong>Confidential Inquiry.</strong><br>No obligation, no fees unless we take your case.
              </div>
           </div>
        </div>
    </div>
    """

def main():
    print("Scanning for cse-meeting-guide.html files...")

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
        
        # If it already has our NEW right sidebar, delete it so we can inject the fresh one
        existing_sidebar = soup.find('div', class_='premium-sidebar-right')
        if existing_sidebar:
            existing_sidebar.decompose()
            
        # Ensure we are wrapping the content correctly
        content_div = soup.find('div', class_='content-body')
        
        # Check if the flex container was created by previous script
        split_container = soup.find('div', class_='premium-split-container')
        
        if split_container:
            # Re-inject the new sidebar into the existing split container
            title_tag = soup.find('title')
            district_name = "New York"
            if title_tag:
                title_text = title_tag.text.strip()
                if 'for ' in title_text:
                    district_name = title_text.split('for ')[-1].strip()
                elif '|' in title_text:
                    district_name = title_text.split('|')[0].strip()
                    
            right_col_soup = BeautifulSoup(get_mini_law_card(district_name), 'html.parser')
            split_container.append(right_col_soup)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            count += 1
            print(f"[SUCCESS] Swapped in Mini Law Card: {file_path}")
            
        elif content_div:
            # Build the layout from scratch if it doesn't exist yet
            title_tag = soup.find('title')
            district_name = "New York"
            if title_tag:
                title_text = title_tag.text.strip()
                if 'for ' in title_text:
                    district_name = title_text.split('for ')[-1].strip()
                elif '|' in title_text:
                    district_name = title_text.split('|')[0].strip()
                    
            # Create inline flexbox container
            split_section = soup.new_tag('div', **{'class': 'premium-split-container', 'style': 'display: flex; flex-wrap: wrap; gap: 40px; align-items: flex-start; width: 100%; margin-top: 30px;'})
            
            # Left column
            left_col = soup.new_tag('div', **{'class': 'content-body', 'style': 'flex: 1 1 60%; min-width: 300px; max-width: 100%; padding: 0; margin-top: 0;'})
            for child in list(content_div.contents):
                left_col.append(child.extract())
                
            # Right column (The Mini Card)
            right_col_soup = BeautifulSoup(get_mini_law_card(district_name), 'html.parser')
            
            # Assemble
            split_section.append(left_col)
            split_section.append(right_col_soup)
            content_div.replace_with(split_section)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            count += 1
            print(f"[SUCCESS] Built layout and injected Mini Law Card: {file_path}")

    print(f"\nDONE! Upgraded {count} pages.")

if __name__ == '__main__':
    main()