# File: fix_broken_css.py
import os
from bs4 import BeautifulSoup

# Target directory
html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"

# Step 1: Find all actual CSS files and map their correct root-relative paths
css_map = {}
for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.css'):
            full_path = os.path.join(root, file)
            # Calculate the path relative to the root of the site
            rel_path = os.path.relpath(full_path, html_dir)
            # Ensure forward slashes and prepend a root slash
            root_relative_path = '/' + rel_path.replace('\\', '/')
            css_map[file] = root_relative_path

# Step 2: Update all HTML files to use the true absolute root paths
for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            modified = False
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                
                # Ignore external stylesheets (CDNs, Google Fonts, etc.)
                if href and not href.startswith(('http://', 'https://', '//')):
                    # Extract just the filename from the broken/relative href
                    css_filename = href.split('/')[-1]
                    
                    # If we mapped this CSS file in Step 1, force the absolute path
                    if css_filename in css_map:
                        correct_href = css_map[css_filename]
                        if href != correct_href:
                            link['href'] = correct_href
                            modified = True
            
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"[FIXED CSS PATHS] {filepath}")