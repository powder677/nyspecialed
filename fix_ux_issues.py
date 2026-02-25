import os
import re
from bs4 import BeautifulSoup

# Define the root directory of the site (current directory)
ROOT_DIR = "."

def fix_css_contrast():
    """Fixes the blue-on-blue contrast issue on guide sub-pages."""
    css_path = os.path.join(ROOT_DIR, 'style.css')
    
    contrast_css = """
/* =========================================================
   UX AUDIT FIX: Contrast & Readability for Guide Pages
   ========================================================= */
main, .guide-content, .district-content, .content-section {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
}

main a, .guide-content a, .district-content a {
    color: #0056b3 !important; /* Accessible high-contrast blue */
    text-decoration: underline;
    font-weight: 600;
}

main h1, main h2, main h3, .guide-content h1, .guide-content h2 {
    color: #111827 !important; 
}
"""
    if os.path.exists(css_path):
        with open(css_path, 'a', encoding='utf-8') as f:
            f.write(contrast_css)
        print("✅ Added high-contrast CSS overrides to style.css")
    else:
        print("⚠️ style.css not found. Creating one with contrast fixes.")
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(contrast_css)

def soften_bureaucratic_copy(html_content):
    """Translates legal jargon to parent-first benefits."""
    replacements = {
        r"Grievance Dispute Resolution": "Resolving School Conflicts",
        r"Evaluation Child Find": "Requesting an Evaluation",
        r"Grievance/Dispute Resolution": "Resolving School Conflicts"
    }
    
    for old, new in replacements.items():
        html_content = re.sub(old, new, html_content, flags=re.IGNORECASE)
    
    return html_content

def update_html_files():
    """Iterates through all HTML files to apply Navigation, Search, and Copy fixes."""
    html_files_processed = 0
    
    for subdir, _, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(subdir, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 1. Soften Copy (Regex is safer for raw text nodes across various tags)
                content = soften_bureaucratic_copy(content)
                
                soup = BeautifulSoup(content, 'html.parser')
                modified = False

                # 2. Consolidate Navigation (Merge Free Resources & Toolkits)
                nav_links = soup.find_all('a')
                has_resources = False
                for a in nav_links:
                    if 'Free Resources' in a.text or 'Resources' in a.text:
                        a.string = "Parent Resources"
                        has_resources = True
                        modified = True
                    if 'Toolkits' in a.text:
                        # Remove the toolkits link if Parent Resources exists to avoid redundancy
                        if has_resources:
                            if a.parent and a.parent.name == 'li':
                                a.parent.decompose() 
                            else:
                                a.decompose()
                            modified = True

                # 3 & 4. Implement Predictive Search & Hero CTA changes (Targeting Homepage/Hero)
                # Look for the massive district dropdown (usually a select with many options)
                select_dropdown = soup.find('select')
                if select_dropdown and len(select_dropdown.find_all('option')) > 10:
                    # Convert <select> to an accessible <input list="..."> predictive search
                    options = select_dropdown.find_all('option')
                    
                    # Create Input
                    search_input = soup.new_tag('input', type='text', id='districtSearch', list='districtList', placeholder='🔍 Find your Texas school district...', style='width: 100%; max-width: 400px; padding: 12px; font-size: 16px; border-radius: 8px; border: 2px solid #ccc;')
                    
                    # Create Datalist
                    datalist = soup.new_tag('datalist', id='districtList')
                    for opt in options:
                        if opt.get('value'): # Skip placeholder options
                            new_opt = soup.new_tag('option', value=opt.get('value'))
                            datalist.append(new_opt)
                    
                    # Insert new tags, remove old select
                    select_dropdown.insert_before(search_input)
                    select_dropdown.insert_before(datalist)
                    
                    # Add vanilla JS to handle the datalist selection routing
                    js_script = soup.new_tag('script')
                    js_script.string = """
                        document.getElementById('districtSearch').addEventListener('input', function(e) {
                            var val = e.target.value;
                            var list = document.getElementById('districtList').childNodes;
                            for (var i = 0; i < list.length; i++) {
                                if (list[i].value === val) {
                                    // Construct URL format assuming value is district slug, adjust if needed
                                    window.location.href = '/districts/' + val.toLowerCase().replace(/\s+/g, '-') + '/index.html';
                                    break;
                                }
                            }
                        });
                    """
                    select_dropdown.insert_after(js_script)
                    select_dropdown.decompose()
                    modified = True

                # Demote secondary CTA (e.g., download checklist) if in Hero
                # Looking for links with heavy button classes
                cta_buttons = soup.find_all('a', class_=re.compile(r'btn|button', re.I))
                for btn in cta_buttons:
                    if 'checklist' in btn.text.lower():
                        # Demote to ghost button styling by modifying inline style or class
                        btn['style'] = "background-color: transparent; color: #0056b3; border: 2px solid #0056b3; padding: 10px 20px; border-radius: 8px; font-weight: 600;"
                        modified = True

                if modified:
                    # Write the changes back to the file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    html_files_processed += 1

    print(f"✅ Processed and updated {html_files_processed} HTML files with UX/UI fixes.")

if __name__ == "__main__":
    print("🚀 Starting UI/UX Audit Fixes...")
    fix_css_contrast()
    update_html_files()
    print("🎉 All fixes applied successfully. Please review the site locally.")