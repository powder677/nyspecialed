# File: fix_internal_links.py
import os
from bs4 import BeautifulSoup

html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
my_domain = "newyorkspecialed.net"

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            modified = False
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # RULE 1: External Links
                if href.startswith(('http://', 'https://')):
                    if my_domain not in href:
                        # Secure the external link
                        if a_tag.get('target') != '_blank':
                            a_tag['target'] = '_blank'
                            modified = True
                        
                        rel_attr = a_tag.get('rel', [])
                        if isinstance(rel_attr, str):
                            rel_attr = rel_attr.split()
                            
                        if 'noopener' not in rel_attr or 'noreferrer' not in rel_attr:
                            a_tag['rel'] = "noopener noreferrer"
                            modified = True
                    continue # Skip internal path formatting for absolute URLs
                
                # RULE 2 & 3: Internal Links (Ignore mailto, tel, JS)
                if href.startswith(('mailto:', 'tel:', 'javascript:')):
                    continue
                
                # Separate URL path from fragment/anchor (e.g., /path/#hash)
                parts = href.split('#', 1)
                path = parts[0]
                fragment = '#' + parts[1] if len(parts) > 1 else ''
                
                if path:
                    original_path = path
                    
                    # Convert .html file links to clean directory paths
                    if path.endswith('.html') and not path.endswith('index.html'):
                        path = path[:-5] + '/'
                    elif path.endswith('index.html'):
                        path = path[:-10] # Strip index.html entirely
                        if not path.endswith('/'):
                            path += '/'
                        
                    # Enforce trailing slash on directories (ignore files with extensions like .pdf, .css)
                    if not path.endswith('/') and '.' not in path.split('/')[-1]:
                        path += '/'
                        
                    # Apply updates if changed
                    if path != original_path:
                        a_tag['href'] = path + fragment
                        modified = True
                        
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"[STANDARDIZED LINKS] {filepath}")

print("Site-wide internal link standardization complete.")