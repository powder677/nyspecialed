import os
import glob
from bs4 import BeautifulSoup

def main():
    # Target all index.html files inside the subdirectories of 'districts'
    # e.g., districts/albany-city-sd/index.html
    index_files = glob.glob('districts/*/index.html')
    
    # CSS required for the Premium Sidebar Card
    sidebar_css = """
<style>
    /* --- PREMIUM SIDEBAR CARD STYLES --- */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');
    
    .premium-card {
      background: #fdfaf5;
      border: 1px solid #d6cbbf;
      border-radius: 6px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0,0,0,0.12);
      font-family: 'DM Sans', sans-serif;
    }
    .card-header {
      background: #002868;
      padding: 22px 24px 18px;
      border-bottom: 3px solid #d4af37;
    }
    .premium-card .eyebrow {
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: #d4af37;
      margin-bottom: 8px;
    }
    .premium-card .title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 26px;
      font-weight: 500;
      color: #f5f0e8;
      line-height: 1.1;
      margin: 0;
    }
    .premium-card .title em {
      font-style: italic;
      color: #e5c158;
    }
    .premium-card .card-body {
      padding: 24px;
    }
    .premium-card .empathy {
      font-family: 'Cormorant Garamond', serif;
      font-size: 20px;
      font-weight: 600;
      color: #002868;
      line-height: 1.4;
      margin-bottom: 12px;
    }
    .premium-card .divider {
      width: 48px;
      height: 2px;
      background: #d4af37;
      margin: 16px 0;
    }
    .premium-card .checklist {
      list-style: none;
      margin: 16px 0;
      padding: 0;
    }
    .premium-card .checklist li {
      font-size: 14px;
      color: #6b5f53;
      padding: 6px 0 6px 20px;
      position: relative;
    }
    .premium-card .checklist li::before {
      content: '§';
      font-family: 'Cormorant Garamond', serif;
      font-size: 16px;
      color: #d4af37;
      position: absolute;
      left: 0;
    }
    .premium-card .premium-btn {
      background: #c8102e;
      color: white;
      border: none;
      padding: 14px;
      border-radius: 4px;
      font-weight: 600;
      font-family: 'DM Sans', sans-serif;
      font-size: 16px;
      cursor: pointer;
      transition: background 0.2s;
      width: 100%;
    }
    .premium-card .premium-btn:hover { background: #a50b24; }
</style>
"""

    def get_sidebar_html(district_name):
        # Generates the sidebar HTML dynamically using the specific district's name
        return f"""
        <div class="sidebar-right" style="flex: 1 1 30%; min-width: 300px; position: sticky; top: 20px; align-self: start;">
            <div class="premium-card">
               <div class="card-header">
                  <p class="eyebrow">{district_name} Expertise</p>
                  <h3 class="title">CSE Meeting <em>Toolkit</em></h3>
               </div>
               
               <div class="card-body">
                  <p class="empathy">
                     Don't walk into your CSE meeting unprepared.
                  </p>
                  
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
                     <button type="submit" class="premium-btn">
                        Get Free Toolkit →
                     </button>
                  </form>
                  
                  <p class="confidential-note" style="font-size: 12px; color: #888; margin-top: 15px; text-align: center;">
                     <strong><i class="fas fa-lock"></i> Privacy guaranteed.</strong> No spam.<br>Unsubscribe anytime.
                  </p>
               </div>
            </div>
        </div>
        """

    count = 0
    for file_path in index_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Skip if already processed to prevent duplicates
        if soup.find('div', class_='sidebar-right'):
            print(f"Skipping {file_path}, already has sidebar layout.")
            continue
            
        # 2. Find the main content section to split
        section = soup.find('section', class_='local-aeo-section')
        if not section:
            print(f"Skipping {file_path}, no 'local-aeo-section' found.")
            continue
            
        # 3. Extract the district name dynamically from the <title> tag
        title_tag = soup.find('title')
        district_name = "New York State"
        if title_tag:
            title_text = title_tag.text.strip()
            if 'Special Ed' in title_text:
                district_name = title_text.split('Special Ed')[0].strip()
            else:
                district_name = title_text.split('|')[0].strip()
                
        # 4. Override old CSS constraints (like max-width: 800px) inline to allow the 70/30 split
        section['style'] = "background: #fff; padding: 40px 20px 60px 20px; max-width: 100% !important;"
        
        # 5. Build the flex container
        container = soup.new_tag('div', **{'class': 'container', 'style': 'max-width: 1200px; margin: 0 auto; display: flex; flex-wrap: wrap; gap: 40px;'})
        
        # 6. Build the left column and move all current content from the section into it
        left_col = soup.new_tag('div', **{'class': 'main-content-left', 'style': 'flex: 1 1 60%; min-width: 300px; line-height: 1.8;'})
        for child in list(section.contents):
            left_col.append(child.extract())
            
        # 7. Build the right column using the generated sidebar HTML
        right_col_soup = BeautifulSoup(get_sidebar_html(district_name), 'html.parser')
        
        # 8. Append both columns to the container, and the container to the section
        container.append(left_col)
        container.append(right_col_soup)
        section.append(container)
        
        # 9. Inject the premium card CSS into the <head>
        head = soup.find('head')
        if head:
            css_soup = BeautifulSoup(sidebar_css, 'html.parser')
            head.append(css_soup)
            
        # 10. Write the updated HTML back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        count += 1
        print(f"Updated {file_path}")

    print(f"\nSuccessfully upgraded {count} silo index pages to the 70/30 layout.")

if __name__ == '__main__':
    main()