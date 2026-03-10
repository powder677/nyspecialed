import os

# Update this if your domain is different!
BASE_URL = "https://www.newyorkspecialed.net"
SITE_DIR = "."
OUTPUT = "sitemap.xml"

# Directories to skip so they don't end up in Google Search
IGNORE_DIRS = {
    "_backups", 
    "components", # Skips your partial HTML files like components-navbar.html
    "output",     # Skips generated markdown files
    "assets", 
    "images", 
    "styles"
}

urls = []

for root, dirs, files in os.walk(SITE_DIR):
    # Modify dirs in-place to skip ignored directories and hidden folders (like .git)
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
    
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            
            # Remove the SITE_DIR prefix (usually '.') and normalize slashes
            url_path = path.replace(SITE_DIR, "", 1).replace("\\", "/")
            
            # Ensure the path starts with a slash
            if not url_path.startswith('/'):
                url_path = '/' + url_path
                
            # Clean up 'index.html' to keep URLs pretty (e.g., /about/index.html -> /about/)
            if url_path.endswith("/index.html"):
                url_path = url_path[:-10] # Removes 'index.html', leaves the trailing '/'
            elif url_path == "/index.html":
                url_path = "/" # Root homepage
                
            urls.append(BASE_URL + url_path)

# Write to sitemap.xml
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

    # Sorting the URLs makes the sitemap easier to read
    for url in sorted(urls):
        f.write("  <url>\n")
        f.write(f"    <loc>{url}</loc>\n")
        f.write("  </url>\n")

    f.write("</urlset>\n")

print(f"Sitemap generated successfully in {OUTPUT} with {len(urls)} URLs!")