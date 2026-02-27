import os
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
SITE_ROOT_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed" # Change to your actual NY site folder
DOMAIN = "https://www.newyorkspecialed.net"

def get_clean_canonical_url(file_path, root_dir):
    """
    Converts a local file path into a clean canonical URL.
    - index.html is stripped out (e.g., /districts/index.html -> /districts/)
    - .html extension is removed (e.g., /guides/cse-meeting-guide.html -> /guides/cse-meeting-guide/)
    """
    # Get the relative path of the file from the root directory
    rel_path = os.path.relpath(file_path, root_dir)
    
    # Convert Windows backslashes to forward slashes for the URL
    url_path = rel_path.replace("\\", "/")
    
    # Clean up index.html and standard .html extensions
    if url_path == "index.html":
        clean_path = "" # Homepage
    elif url_path.endswith("/index.html"):
        clean_path = url_path.replace("index.html", "") # Keep the trailing slash for directories
    elif url_path.endswith(".html"):
        # For standard files, remove .html and add a trailing slash (standard practice)
        clean_path = url_path.replace(".html", "/")
    else:
        clean_path = url_path
        
    # Construct full canonical URL
    if clean_path:
        return f"{DOMAIN}/{clean_path}"
    else:
        return f"{DOMAIN}/"

def inject_canonical_tags(root_dir):
    updated_count = 0
    
    # Walk through all directories and files
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".html"):
                file_path = os.path.join(dirpath, filename)
                canonical_url = get_clean_canonical_url(file_path, root_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        soup = BeautifulSoup(file, 'html.parser')
                    
                    # Check if head exists
                    if not soup.head:
                        print(f"⚠ No <head> found in {file_path}. Skipping.")
                        continue
                        
                    # Check if a canonical tag already exists
                    existing_canonical = soup.find('link', rel='canonical')
                    if existing_canonical:
                        if existing_canonical.get('href') == canonical_url:
                            # It's already correct, do nothing
                            continue
                        else:
                            # Update existing wrong canonical tag
                            existing_canonical['href'] = canonical_url
                            print(f"Updated existing canonical in: {file_path}")
                    else:
                        # Create and append new canonical tag
                        new_link = soup.new_tag("link", rel="canonical", href=canonical_url)
                        soup.head.append(new_link)
                        print(f"Added new canonical to: {file_path}")
                    
                    # Save the modified HTML back to the file
                    with open(file_path, 'w', encoding='utf-8') as file:
                        # formatter="html" prevents self-closing tags from getting messed up
                        file.write(soup.prettify(formatter="html"))
                        
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")

    print(f"\n✅ Finished! Updated canonical tags in {updated_count} files.")

if __name__ == "__main__":
    if not os.path.exists(SITE_ROOT_DIR):
        print(f"Directory not found: {SITE_ROOT_DIR}")
    else:
        print(f"Scanning {SITE_ROOT_DIR} for HTML files...")
        inject_canonical_tags(SITE_ROOT_DIR)