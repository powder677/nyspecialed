# File: generate_pristine_sitemap.py
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
base_url = "https://www.newyorkspecialed.net"
output_sitemap = os.path.join(html_dir, "sitemap.xml")

urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
added_urls = set()

for root, dirs, files in os.walk(html_dir):
    # Skip component or include directories
    if 'components' in root.split(os.sep):
        continue
        
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                
            # Only include pages that have a canonical tag
            canonical_tag = soup.find('link', rel='canonical')
            
            if canonical_tag and canonical_tag.has_attr('href'):
                loc_url = canonical_tag['href']
                
                # Exclude explicitly non-indexed pages
                robots_tag = soup.find('meta', attrs={'name': 'robots'})
                if robots_tag and 'noindex' in robots_tag.get('content', '').lower():
                    continue
                
                # Prevent duplicates
                if loc_url not in added_urls and loc_url.startswith(base_url):
                    url = ET.SubElement(urlset, 'url')
                    loc = ET.SubElement(url, 'loc')
                    loc.text = loc_url
                    lastmod = ET.SubElement(url, 'lastmod')
                    lastmod.text = datetime.today().strftime('%Y-%m-%d')
                    added_urls.add(loc_url)

# Write out the clean XML file
tree = ET.ElementTree(urlset)
ET.indent(tree, space="\t", level=0)
tree.write(output_sitemap, encoding='utf-8', xml_declaration=True)

print(f"SUCCESS: Clean sitemap generated at {output_sitemap} with {len(added_urls)} pristine URLs.")