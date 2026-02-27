import os
import pandas as pd
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
SITE_ROOT_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed" # Your site folder
CSV_FILE_PATH = "newyorkspecialed_27-feb-2026_links_2026-02-27_14-58-57.csv"

# REPLACE THIS WITH THE ACTUAL, CORRECT URL PATH
# E.g., "/guides/parent-advocacy-guide/index.html" or "https://www.newyorkspecialed.net/guides/..."
NEW_CORRECT_LINK = "/guides/parent-advocacy-guide.html" 

# The broken URL we need to find and replace
BROKEN_LINK_TARGET = "parent-advocacy-guide.html"


def get_local_file_path(source_url, root_dir):
    """
    Tries to map the live website URL from the CSV back to your local computer's HTML file.
    """
    # Remove the domain part
    url_path = source_url.replace("https://www.newyorkspecialed.net/", "")
    url_path = url_path.strip("/")
    
    # It could be either a direct .html file or an index.html inside a folder
    path_option_1 = os.path.join(root_dir, f"{url_path}.html")
    path_option_2 = os.path.join(root_dir, url_path, "index.html")
    
    # Convert to Windows paths to safely check
    path_option_1 = os.path.normpath(path_option_1)
    path_option_2 = os.path.normpath(path_option_2)
    
    if os.path.exists(path_option_1):
        return path_option_1
    elif os.path.exists(path_option_2):
        return path_option_2
    else:
        return None

def fix_broken_links():
    # 1. Read ONLY the specific links from the CSV
    df = pd.read_csv(CSV_FILE_PATH)
    
    # 2. Filter down to just the 404 errors (just to be safe)
    broken_links = df[df['Target HTTP status code'] == 404]
    
    if broken_links.empty:
        print("No 404 broken links found in the CSV!")
        return

    updated_count = 0
    
    # 3. Loop through the specific source URLs that have the broken link
    for _, row in broken_links.iterrows():
        source_url = row['Source URL']
        local_file = get_local_file_path(source_url, SITE_ROOT_DIR)
        
        if not local_file:
            print(f"⚠ Could not find local HTML file for: {source_url}")
            continue
            
        try:
            with open(local_file, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                
            links_changed = False
            
            # Find all <a> tags
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # If the href points to the broken link, replace it
                if BROKEN_LINK_TARGET in href:
                    a_tag['href'] = NEW_CORRECT_LINK
                    links_changed = True
            
            # Save the file if we made a change
            if links_changed:
                with open(local_file, 'w', encoding='utf-8') as file:
                    file.write(soup.prettify(formatter="html"))
                print(f"✅ Fixed link in: {local_file}")
                updated_count += 1
            else:
                print(f"➖ Link already fixed or not found in HTML for: {local_file}")
                
        except Exception as e:
            print(f"❌ Error processing {local_file}: {e}")

    print(f"\n🎉 Done! Fixed the broken link in {updated_count} specific files based on your CSV.")

if __name__ == "__main__":
    fix_broken_links()