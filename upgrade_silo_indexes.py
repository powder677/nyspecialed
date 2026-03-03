import os
from bs4 import BeautifulSoup

def main():
    print("Scanning for index.html files in district folders...")

    def get_sidebar_html(district_name):
        return f"""
        <div class="premium-sidebar-right">
            <div class="premium-card">
               <div class="card-header">
                  <p class="eyebrow">{district_name} Expertise</p>
                  <h3 class="title">CSE Meeting <em>Toolkit</em></h3>
               </div>
               
               <div class="card-body">
                  <p class="empathy">Don't walk into your CSE meeting unprepared.</p>
                  <div class="divider"></div>
                  <p class="copy" style="font-size: 15px; color: #6b5f53; margin-bottom: 15px;">
                     Get the exact email templates, timeline checklists, 
                     and red-flag warnings used by experienced advocates.
                  </p>
                  <ul class="checklist">
                     <li>Evaluation request template</li>
                     <li>60-day timeline tracker</li>
                     <li>CSE meeting preparation checklist</li>
                     <li>IEE request letter sample</li>
                  </ul>
                  <form action="#" method="POST" style="display: flex; flex-direction: column; gap: 12px; margin-top: 25px;">
                     <input type="email" placeholder="Your best email address" required style="padding: 14px; border: 1px solid #d6cbbf; border-radius: 4px; font-family: 'DM Sans', sans-serif; font-size: 15px; outline: none;" />
                     <button type="submit" class="premium-btn">Get Free Toolkit →</button>
                  </form>
                  <p class="confidential-note" style="font-size: 12px; color: #888; margin-top: 15px; text-align: center;">
                     <strong><i class="fas fa-lock"></i> Privacy guaranteed.</strong> No spam.<br>Unsubscribe anytime.
                  </p>
               </div>
            </div>
        </div>
        """

    files_to_process = []
    for root, dirs, files in os.walk('.'):
        parts = root.split(os.sep)
        if 'districts' in parts and parts[-1] != 'districts':
            if 'index.html' in files:
                files_to_process.append(os.path.join(root, 'index.html'))
                
    if not files_to_process:
        print("ERROR: Could not find any district index.html files.")
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
            
        # Find the old section
        section = soup.find('section', class_='local-aeo-section')
        if not section:
            print(f"[SKIPPED] {file_path} - Needs manual check (no local-aeo-section found).")
            continue
            
        # Extract the district name dynamically from <title>
        title_tag = soup.find('title')
        district_name = "New York State"
        if title_tag:
            title_text = title_tag.text.strip()
            if 'Special Ed' in title_text:
                district_name = title_text.split('Special Ed')[0].strip()
            else:
                district_name = title_text.split('|')[0].strip()
                
        # Detach from the old 800px CSS rules
        section['class'] = 'premium-split-section'
        
        # Build the new layout containers
        container = soup.new_tag('div', **{'class': 'premium-split-container'})
        left_col = soup.new_tag('div', **{'class': 'premium-content-left'})
        
        # Move all contents into the left column
        for child in list(section.contents):
            left_col.append(child.extract())
            
        # Generate the Sidebar HTML
        right_col_soup = BeautifulSoup(get_sidebar_html(district_name), 'html.parser')
        
        # Append columns to the container, and container to the section
        container.append(left_col)
        container.append(right_col_soup)
        section.append(container)
            
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        count += 1
        print(f"[SUCCESS] Upgraded HTML structure: {file_path}")

    print(f"\nDONE! Upgraded {count} pages.")

if __name__ == '__main__':
    main()