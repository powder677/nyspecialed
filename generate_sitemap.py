#!/usr/bin/env python3
import os
import re
import argparse
from datetime import datetime
from bs4 import BeautifulSoup

def generate_sitemap(dry_run=False):
    # Resolve root relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = script_dir  # Assuming script is at repo root
    
    excluded_dirs = {'components', 'assets', 'images', 'styles', 'output', '.git'}
    urls = []
    skipped_count = 0
    
    print(f"Scanning directory: {root_dir}")
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to prune excluded directories
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs and not d.startswith('.')]
        
        for filename in filenames:
            if not filename.endswith('.html') or filename.endswith('.bak'):
                continue
                
            file_path = os.path.join(dirpath, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for noindex
            robots_meta = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'robots'})
            if robots_meta:
                content_attr = robots_meta.get('content', '').lower()
                if 'noindex' in content_attr:
                    skipped_count += 1
                    continue
                    
            # Get canonical tag
            canonical_tag = soup.find('link', attrs={'rel': lambda x: x and x.lower() == 'canonical'})
            if not canonical_tag or not canonical_tag.get('href'):
                skipped_count += 1
                continue
                
            canonical_url = canonical_tag['href'].strip()
            
            # Get last modified (mtime)
            mtime = os.path.getmtime(file_path)
            lastmod = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            
            urls.append((canonical_url, lastmod))
            
    # Build sitemap XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for url, lastmod in sorted(urls):
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url}</loc>')
        xml_lines.append(f'    <lastmod>{lastmod}</lastmod>')
        xml_lines.append('  </url>')
    xml_lines.append('</urlset>')
    new_sitemap_content = '\n'.join(xml_lines) + '\n'
    
    sitemap_path = os.path.join(root_dir, 'sitemap.xml')
    
    # Read existing sitemap for diff
    old_sitemap_content = ""
    if os.path.exists(sitemap_path):
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            old_sitemap_content = f.read()
            
    print(f"\n--- SITEMAP GENERATION SUMMARY ---")
    print(f"Total valid URLs found: {len(urls)}")
    print(f"Skipped (noindex, missing canonical, or excluded): {skipped_count}")
    
    if old_sitemap_content.strip() == new_sitemap_content.strip():
        print("Result: Sitemap is identical to existing sitemap.xml.")
    else:
        print("Result: Sitemap differs from existing sitemap.xml.")
        
    if dry_run:
        print("\n[DRY RUN] sitemap.xml was NOT written to disk.")
    else:
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(new_sitemap_content)
        print(f"Successfully wrote updated sitemap to {sitemap_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate pristine sitemap from canonical tags.")
    parser.add_argument('--dry-run', action='store_true', help="Show output summary without writing files.")
    args = parser.parse_args()
    generate_sitemap(dry_run=args.dry_run)