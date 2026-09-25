import os
import csv
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def load_broken_paths(csv_path="404_report.csv"):
    """Extracts all dead URLs and relative paths from the crawler CSV report."""
    broken_targets = set()
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found in the current directory.")
        return broken_targets
        
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL', '').strip()
            if url:
                broken_targets.add(url)
                parsed = urlparse(url)
                if parsed.path:
                    broken_targets.add(parsed.path)
                    # Add path variations for robust matching (with/without trailing slashes)
                    broken_targets.add(parsed.path.rstrip('/'))
                    broken_targets.add(parsed.path + '/')
                    
    return broken_targets

def fix_broken_links_in_site(root_dir=".", csv_path="404_report.csv"):
    broken_targets = load_broken_paths(csv_path)
    if not broken_targets:
        print("No 404 targets loaded. Exiting.")
        return

    modified_count = 0
    link_fix_count = 0

    print(f"Loaded {len(broken_targets)} URL patterns to check. Scanning HTML files...")

    # Recursively walk through all directories and subdirectories
    for subdir, dirs, files in os.walk(root_dir):
        # Skip hidden/system directories like .git
        if '.git' in subdir:
            continue
            
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(subdir, file)
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                soup = BeautifulSoup(content, 'html.parser')
                changed = False
                
                # Check all anchor tags for matching 404 links
                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    
                    # Determine if href matches any broken URL or path
                    is_broken = False
                    if href in broken_targets:
                        is_broken = True
                    else:
                        # Check path matching relative vs absolute
                        parsed_href = urlparse(href)
                        href_path = parsed_href.path if parsed_href.path else href
                        if href_path in broken_targets or href_path.rstrip('/') in broken_targets:
                            is_broken = True
                            
                    if is_broken:
                        # If the link is inside a navigation list item (li), remove the whole li
                        li = a.find_parent('li')
                        if li and len(li.get_text(strip=True)) < 50: # safe check to avoid deleting large sections
                            li.decompose()
                        else:
                            # Otherwise, unwrap the anchor tag (keeps the text, removes the broken link)
                            a.unwrap()
                        
                        changed = True
                        link_fix_count += 1

                # Save the file only if changes were made
                if changed:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    modified_count += 1
                    print(f"Fixed broken links in: {filepath}")

    print(f"\nDone! Successfully fixed {link_fix_count} broken links across {modified_count} HTML files.")

if __name__ == '__main__':
    fix_broken_links_in_site(".", "404_report.csv")