import os
import csv
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def run_diagnostic_and_fix(root_dir=".", csv_path="404_report.csv"):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # 1. Load all broken URLs and normalize paths
    broken_targets = set()
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL', '').strip()
            if url:
                broken_targets.add(url)
                parsed = urlparse(url)
                if parsed.path:
                    broken_targets.add(parsed.path)
                    broken_targets.add(parsed.path.rstrip('/'))
                    broken_targets.add(parsed.path + '/')
                    # Also add relative version without leading slash
                    if parsed.path.startswith('/'):
                        broken_targets.add(parsed.path.lstrip('/'))

    print(f"Loaded {len(broken_targets)} target patterns from CSV.")

    # 2. Walk through the project directories
    html_files = []
    for subdir, dirs, files in os.walk(root_dir):
        if '.git' in subdir or 'node_modules' in subdir:
            continue
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(subdir, file))

    print(f"Found {len(html_files)} HTML files to scan across directories.")

    modified_count = 0
    link_fix_count = 0

    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        changed = False
        
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            
            # Check against broken targets
            is_broken = False
            parsed_href = urlparse(href)
            href_path = parsed_href.path if parsed_href.path else href
            
            if (href in broken_targets or 
                href_path in broken_targets or 
                href_path.rstrip('/') in broken_targets or
                '/' + href_path.lstrip('/') in broken_targets):
                is_broken = True

            if is_broken:
                print(f"[{filepath}] Found broken link: {href}")
                li = a.find_parent('li')
                if li and len(li.get_text(strip=True)) < 80:
                    li.decompose()
                else:
                    a.unwrap()
                changed = True
                link_fix_count += 1

        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            modified_count += 1

    print(f"\nScan complete. Fixed {link_fix_count} broken links across {modified_count} files.")

if __name__ == '__main__':
    # Make sure to point this to your actual project root directory if running from elsewhere
    run_diagnostic_and_fix(".", "404_report.csv")