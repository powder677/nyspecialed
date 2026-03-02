# File: fix_district_hubs.py
import os
import re

# Your local repository path
html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\districts"

# Map the broken relative district links to the actual global guides
link_mapping = {
    r'href=["\']cse-meeting-guide/?["\']': 'href="/guides/cse-meeting-guide/"',
    r'href=["\']evaluation-process/?["\']': 'href="/guides/evaluation-request-ny/"',
    r'href=["\']discipline-rights/?["\']': 'href="/guides/dispute-resolution-ny/"',
    r'href=["\']parent-advocacy-guide/?["\']': 'href="/guides/parent-advocacy-guide/"',
    r'href=["\']/?["\'] class=["\']active["\']': 'href="/" class="active"' # Fixes the broken 'District Home' link
}

files_patched = 0

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file == 'index.html':
            filepath = os.path.join(root, file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
                
            modified = False
            
            # Apply the routing patches
            for broken_pattern, fixed_link in link_mapping.items():
                if re.search(broken_pattern, html, flags=re.IGNORECASE):
                    html = re.sub(broken_pattern, fixed_link, html, flags=re.IGNORECASE)
                    modified = True
                    
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
                files_patched += 1
                print(f"[PATCHED HUB LINKS] {os.path.relpath(filepath, html_dir)}")

print(f"Complete. Rerouted broken hub links across {files_patched} district pages.")