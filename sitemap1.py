import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from datetime import datetime

class SitemapGenerator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.urls_to_visit = [base_url]
        self.session = requests.Session()
        # Pretend to be a standard browser to avoid basic bot blocks
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

    def normalize_url(self, url):
        """Removes fragments and normalizes trailing slashes for deduplication."""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if normalized.endswith('/') and len(normalized) > len(self.base_url):
            normalized = normalized[:-1]
        return normalized

    def get_links_from_page(self, url):
        """Fetches a page and extracts all internal links."""
        try:
            response = self.session.get(url, timeout=10)
            # Only process HTML pages
            if 'text/html' not in response.headers.get('Content-Type', ''):
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                parsed_href = urlparse(full_url)
                
                # Keep only HTTP/HTTPS and internal links to the same domain
                if parsed_href.scheme in ('http', 'https') and parsed_href.netloc == self.domain:
                    clean_url = self.normalize_url(full_url)
                    links.append(clean_url)
            return links
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return []

    def crawl(self, max_pages=3500):
        """Crawls the website up to the max_pages limit."""
        print(f"Starting crawl for {self.base_url}...")
        
        while self.urls_to_visit and len(self.visited_urls) < max_pages:
            current_url = self.urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            print(f"Crawling: {current_url}")
            self.visited_urls.add(current_url)
            
            new_links = self.get_links_from_page(current_url)
            for link in new_links:
                if link not in self.visited_urls and link not in self.urls_to_visit:
                    self.urls_to_visit.append(link)

    def calculate_priority(self, url):
        """Assigns priority based on URL depth to reflect information architecture."""
        path = urlparse(url).path
        depth = path.count('/') - 1 if path.endswith('/') else path.count('/')
        
        if depth == 0 or depth == -1:
            return "1.0" # Homepage
        elif depth == 1:
            return "0.8" # Top-level categories / Hubs
        elif depth == 2:
            return "0.6" # Sub-categories / Standard pages
        else:
            return "0.5" # Deep pages

    def generate_xml(self, output_filename="sitemap.xml"):
        """Generates the GSC-compliant XML file."""
        print(f"\nGenerating {output_filename}...")
        
        # Define GSC namespace
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        
        today = datetime.now().strftime('%Y-%m-%d')

        for url in sorted(self.visited_urls):
            url_element = ET.SubElement(urlset, "url")
            
            loc = ET.SubElement(url_element, "loc")
            loc.text = url
            
            lastmod = ET.SubElement(url_element, "lastmod")
            lastmod.text = today
            
            priority = ET.SubElement(url_element, "priority")
            priority.text = self.calculate_priority(url)

        # Write to file with XML declaration
        tree = ET.ElementTree(urlset)
        ET.indent(tree, space="\t", level=0) # Pretty-print for readability
        tree.write(output_filename, encoding="utf-8", xml_declaration=True)
        print(f"Success! Sitemap saved as {output_filename} with {len(self.visited_urls)} URLs.")

# --- Execution ---
if __name__ == "__main__":
    # 1. Replace with your target website
    TARGET_URL = "https://www.newyorkspecialed.net" 
    
    # 2. Initialize and run
    generator = SitemapGenerator(TARGET_URL)
    
    # Optional: adjust max_pages if you have a massive site
    generator.crawl(max_pages=3500) 
    
    # 3. Output the file
    generator.generate_xml("sitemap.xml")