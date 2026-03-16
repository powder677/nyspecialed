import os
from bs4 import BeautifulSoup

# Scan the current directory
WEBSITE_ROOT_DIR = '.'

def patch_district_links(root_dir):
    files_modified = 0
    files_scanned = 0
    
    # Walk the entire repository, not just the districts folder
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                files_scanned += 1
                
                # Figure out if this file is inside a specific district folder
                # Example path: .\districts\albany-city-sd\index.html
                path_parts = filepath.split(os.sep)
                district_slug = None
                
                if 'districts' in path_parts:
                    districts_idx = path_parts.index('districts')
                    # If there is a folder AFTER 'districts', that's our slug
                    if len(path_parts) > districts_idx + 2:
                        district_slug = path_parts[districts_idx + 1]
                
                modified = process_html_file(filepath, district_slug)
                if modified:
                    files_modified += 1

    print(f"\n--- Scan Report ---")
    print(f"Total HTML files scanned: {files_scanned}")
    print(f"Successfully patched: {files_modified} files.")

    if files_scanned == 0:
        print("\n[ALERT] 0 HTML files were found. Are you using a framework like React, Next.js, or Astro?")
        print("If so, your source files are likely .js, .jsx, .ts, or .astro, NOT .html.")

def process_html_file(filepath, district_slug):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except Exception as e:
        return False

    has_changes = False
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # Look for any link that contains 'districts/' and ends with '.html'
        if 'districts/' in href and href.endswith('.html'):
            parts = href.split('/')
            
            # Check if the folder immediately preceding the filename is exactly "districts"
            # This catches:
            # - /districts/discipline-rights.html
            # - https://www.newyorkspecialed.net/districts/discipline-rights.html
            # But safely IGNORES already correct links like: /districts/albany-city-sd/discipline-rights.html
            if len(parts) >= 2 and parts[-2] == 'districts':
                filename = parts[-1]
                
                if not district_slug:
                    # Found a broken link on a page outside a district folder (e.g., the homepage)
                    print(f"[WARNING] Broken link found on global page (Cannot auto-inject slug): {filepath} -> {href}")
                    continue
                    
                # Fix the link by injecting the local directory's slug
                new_href = f"/districts/{district_slug}/{filename}"
                a_tag['href'] = new_href
                has_changes = True
                print(f"[FIXED] {os.path.basename(filepath)} | {href} -> {new_href}")

    if has_changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
        
    return False

if __name__ == "__main__":
    print("Initializing Aggressive SEO Link Repair...")
    patch_district_links(WEBSITE_ROOT_DIR)