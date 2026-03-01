# File: audit_seo_fixes.py
import os
import csv
from bs4 import BeautifulSoup

html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
output_csv = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\seo_audit_report.csv"

audit_results = []

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, html_dir)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            # 1. Check Title Length
            title_tag = soup.find('title')
            title_text = title_tag.string.strip() if title_tag and title_tag.string else ""
            title_pass = 0 < len(title_text) <= 65

            # 2. Check Meta Description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            desc_text = meta_desc['content'].strip() if meta_desc and meta_desc.has_attr('content') else ""
            desc_pass = len(desc_text) >= 70

            # 3. Check H1 Presence
            h1_tag = soup.find('h1')
            h1_pass = bool(h1_tag and h1_tag.text.strip())

            # 4. Check CSS Paths (ensure they are absolute, starting with '/')
            css_pass = True
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href', '')
                if href and not href.startswith(('http://', 'https://', '//')):
                    if not href.startswith('/'):
                        css_pass = False
                        break

            # 5. Check Open Graph Tags
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            og_pass = bool(og_title)

            audit_results.append({
                'File': rel_path,
                'Title Pass (<=65 chars)': title_pass,
                'Desc Pass (>=70 chars)': desc_pass,
                'H1 Pass (Exists)': h1_pass,
                'CSS Pass (Absolute)': css_pass,
                'OG Tags Pass': og_pass
            })

# Write results to CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['File', 'Title Pass (<=65 chars)', 'Desc Pass (>=70 chars)', 'H1 Pass (Exists)', 'CSS Pass (Absolute)', 'OG Tags Pass'])
    writer.writeheader()
    writer.writerows(audit_results)

print(f"Audit complete. Reviewed {len(audit_results)} files.")
print(f"Report saved to: {output_csv}")