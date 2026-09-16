#!/usr/bin/env python3
import os
import argparse
from bs4 import BeautifulSoup

# ==========================================
# DECISION NEEDED: Set choice to 'A' or 'B'
# A: Replace with '/guides/es/index.html'
# B: Remove the link entirely
# ==========================================
CHOICE = 'A'  # Update this once you pick A or B

def fix_nav(dry_run=True):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    modified_files = 0
    
    print(f"Searching for dead /es/distritos/ links (Strategy: Option {CHOICE})...")
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in {'components', 'assets', 'images', 'styles', 'output', '.git'} and not d.startswith('.')]
        
        for filename in filenames:
            if not filename.endswith('.html'):
                continue
            file_path = os.path.join(dirpath, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if '/es/distritos' not in content:
                continue
                
            soup = BeautifulSoup(content, 'html.parser')
            changed = False
            
            for a_tag in soup.find_all('href' if False else 'a', href=lambda h: h and '/es/distritos' in h):
                if CHOICE == 'A':
                    old_href = a_tag['href']
                    # Keep any subpath or anchor if applicable, or map to guides hub
                    a_tag['href'] = '/guides/es/index.html'
                    print(f"[{filename}] Updated href '{old_href}' -> '/guides/es/index.html'")
                    changed = True
                elif CHOICE == 'B':
                    print(f"[{filename}] Removing link: {a_tag.get_text(strip=True)}")
                    a_tag.decompose()
                    changed = True
                    
            if changed:
                modified_files += 1
                new_content = str(soup)
                if not dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
    print(f"\nTotal files affected: {modified_files}")
    if dry_run:
        print("[DRY RUN] No files were modified.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    fix_nav(dry_run=args.dry_run)