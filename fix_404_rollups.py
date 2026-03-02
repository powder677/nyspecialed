# File: fix_404_rollups.py
import os
import csv
import re

html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
csv_file = "newyorkspecialed_01-mar-2026_404-page_2026-03-01_19-04-19.csv"
base_url = "https://www.newyorkspecialed.net"

# Step 1: Read the 404 URLs and create a mapping to their parent directories
link_fixes = {}

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        url = row.get('URL')
        if url and url.startswith(base_url):
            # Extract the relative path (e.g., /districts/buffalo-city-sd/special-ed-updates/)
            broken_path = url.replace(base_url, "")
            
            # Find the parent directory to roll it up to
            # e.g. /districts/buffalo-city-sd/special-ed-updates/ -> /districts/buffalo-city-sd/
            path_parts = [p for p in broken_path.split('/') if p]
            if len(path_parts) > 1:
                parent_path = '/' + '/'.join(path_parts[:-1]) + '/'
                link_fixes[broken_path] = parent_path
                
                # Also map the non-trailing slash version just in case it exists in the HTML
                link_fixes[broken_path.rstrip('/')] = parent_path

print(f"Loaded {len(link_fixes)} broken link mappings. Commencing bulk patch...")

# Step 2: Iterate through all HTML files and replace the broken hrefs
files_modified = 0

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
            
            modified = False
            
            # Search and replace mapped broken links
            for broken, fixed in link_fixes.items():
                # Regex to safely replace the exact href value
                pattern = r'(href=["\'])(' + re.escape(broken) + r')(["\'])'
                
                if re.search(pattern, html):
                    html = re.sub(pattern, r'\g<1>' + fixed + r'\g<3>', html)
                    modified = True
            
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
                files_modified += 1
                print(f"[PATCHED 404 LINKS] {os.path.relpath(filepath, html_dir)}")

print(f"Complete. Patched broken links across {files_modified} files.")