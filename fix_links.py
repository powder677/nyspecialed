import os
import pandas as pd
from bs4 import BeautifulSoup

def deploy_fix(csv_path, website_directory):
    df = pd.read_csv(csv_path)
    
    # Build a robust map to catch both relative and absolute links
    corrections_map = {}
    for url, found_at in zip(df['URL'], df['First found at']):
        broken_path = url.replace("https://www.newyorkspecialed.net", "")
        correct_path = found_at.replace("https://www.newyorkspecialed.net", "")
        
        if broken_path + ".html" == correct_path:
            # Match standard relative paths (e.g., /districts/...)
            corrections_map[broken_path] = correct_path
            # Match full absolute URLs (e.g., https://www.newyorkspecialed.net/...)
            corrections_map[url] = found_at
            # Match relative paths without leading slash
            corrections_map[broken_path.lstrip('/')] = correct_path.lstrip('/')

    html_files_found = 0
    fixed_count = 0

    # Walk through the directory
    for root, _, files in os.walk(website_directory):
        for file in files:
            # If you are using PHP or another file type, change/add it here
            if file.endswith('.html'):
                html_files_found += 1
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                    
                    modified = False
                    # Find all links (a tags, canonical links, etc.)
                    for tag in soup.find_all(['a', 'link'], href=True):
                        href = tag['href']
                        
                        if href in corrections_map:
                            tag['href'] = corrections_map[href]
                            modified = True
                            fixed_count += 1
                    
                    if modified:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                            print(f"Patched link(s) in: {filepath}")
                except Exception as e:
                    pass # Skip unreadable files

    print("\n--- Diagnostics Report ---")
    print(f"Files scanned: {html_files_found} HTML files found in '{os.path.abspath(website_directory)}'")
    print(f"Links patched: {fixed_count} broken links successfully updated.")

if __name__ == "__main__":
    CSV_FILE = "newyorkspecialed_28-feb-2026_404-page_2026-02-28_21-22-54.csv"
    
    # Changed from "./public" to "." to scan your entire current github folder
    WEBSITE_FOLDER = "." 
    
    deploy_fix(CSV_FILE, WEBSITE_FOLDER)