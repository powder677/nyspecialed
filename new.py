import os
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
SITE_ROOT_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
DOMAIN = "https://www.newyorkspecialed.net"

def get_clean_canonical_url(file_path, root_dir):
    rel_path = os.path.relpath(file_path, root_dir)
    url_path = rel_path.replace("\\", "/")
    
    if url_path == "index.html":
        clean_path = "" # Homepage
    elif url_path.endswith("/index.html"):
        # Keeps the trailing slash for directories (e.g., /districts/nys-overview/)
        clean_path = url_path.replace("index.html", "") 
    elif url_path.endswith(".html"):
        # Safely remove exactly '.html' from the end, NO trailing slash
        clean_path = url_path[:-5] 
    else:
        clean_path = url_path
        
    if clean_path:
        return f"{DOMAIN}/{clean_path}"
    else:
        return f"{DOMAIN}/"

def inject_canonical_tags(root_dir):
    updated_count = 0
    
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".html"):
                file_path = os.path.join(dirpath, filename)
                canonical_url = get_clean_canonical_url(file_path, root_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        soup = BeautifulSoup(file, 'html.parser')
                    
                    if not soup.head:
                        print(f"⚠ No <head> found in {file_path}. Skipping.")
                        continue
                        
                    existing_canonical = soup.find('link', rel='canonical')
                    if existing_canonical:
                        if existing_canonical.get('href') == canonical_url:
                            continue
                        else:
                            existing_canonical['href'] = canonical_url
                            print(f"Updated existing canonical in: {file_path}")
                    else:
                        new_link = soup.new_tag("link", rel="canonical", href=canonical_url)
                        soup.head.append(new_link)
                        print(f"Added new canonical to: {file_path}")
                    
                    # Using str(soup) instead of prettify() to prevent HTML formatting corruption
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(str(soup))
                        
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")

    print(f"\n✅ Finished! Safely updated canonical tags in {updated_count} files.")

if __name__ == "__main__":
    if not os.path.exists(SITE_ROOT_DIR):
        print(f"Directory not found: {SITE_ROOT_DIR}")
    else:
        print(f"Scanning {SITE_ROOT_DIR} for HTML files...")
        inject_canonical_tags(SITE_ROOT_DIR)