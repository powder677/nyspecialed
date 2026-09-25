import os
from bs4 import BeautifulSoup

def clean_html_files(root_dir="."):
    modified_count = 0
    
    # Walk through all directories and subdirectories
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(subdir, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                soup = BeautifulSoup(content, 'html.parser')
                changed = False
                
                # 1. Remove "Tools" / "Toolkit" navigation links (both <a> tags with href="/tools/" or text matching Tools/Toolkit in navs)
                nav_elements = soup.select('.site-nav a, .nav-links a, .mobile-menu a, .district-subnav a')
                for a in nav_elements:
                    href = a.get('href', '')
                    text = a.get_text().strip().lower()
                    if '/tools/' in href or 'tools' in text or 'toolkit' in text:
                        li = a.find_parent('li')
                        if li:
                            li.decompose()
                        else:
                            a.decompose()
                        changed = True

                # 2. Remove the Legal Referral offer box on partners pages (or anywhere it appears)
                law_card = soup.find(id='largeLawFirmCard') or soup.find('div', class_='large-law-card')
                if law_card:
                    law_card.decompose()
                    changed = True

                # Save the file only if changes were made
                if changed:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    modified_count += 1
                    print(f"Cleaned: {filepath}")

    print(f"\nDone! Successfully processed and updated {modified_count} HTML files.")

if __name__ == '__main__':
    # Run this from the root folder of your 550-page project
    clean_html_files(".")