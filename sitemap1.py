import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin, urldefrag
from datetime import datetime

class CanonicalSitemapGenerator:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.canonical_urls = set()
        self.urls_to_visit = [self.base_url]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36'
        })
        
        # Diagnostic counters
        self.stats = {
            "crawled": 0,
            "non_canonical_excluded": 0,
            "noindex_excluded": 0,
            "redirects_excluded": 0,
            "external_or_non_html": 0,
            "duplicates_removed": 0
        }

    def process_page(self, url):
        """Fetches page, checks status/headers, reads canonical tag and noindex."""
        try:
            # Allow redirects to track final destination
            response = self.session.get(url, timeout=10, allow_redirects=True)
            self.stats["crawled"] += 1

            # Check if it redirected to a different URL/domain
            final_url = response.url.rstrip("/")
            if urlparse(final_url).netloc != self.domain:
                self.stats["external_or_non_html"] += 1
                return []

            # Only process HTML pages
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                self.stats["external_or_non_html"] += 1
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. Check for 'noindex' in meta robots
            meta_robots = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'robots'})
            if meta_robots and 'noindex' in meta_robots.get('content', '').lower():
                self.stats["noindex_excluded"] += 1
                print(f"  [Skipped: noindex] {url}")
                return []

            # 2. Extract and resolve Canonical Tag
            canonical_tag = soup.find('link', attrs={'rel': lambda x: x and x.lower() == 'canonical'})
            if canonical_tag and canonical_tag.get('href'):
                raw_canonical = canonical_tag['href']
                # Resolve relative canonicals if any
                resolved_canonical = urljoin(final_url, raw_canonical)
                clean_canonical, _ = urldefrag(resolved_canonical)
                clean_canonical = clean_canonical.rstrip("/")

                # Ensure canonical belongs to our target domain
                if urlparse(clean_canonical).netloc != self.domain:
                    self.stats["non_canonical_excluded"] += 1
                    return []

                # If the page's canonical URL doesn't match where it was served, 
                # it means this page is a variant/duplicate pointing elsewhere.
                # Standard SEO best practice: do not put non-self-referencing canonicals in the sitemap.
                if clean_canonical != final_url:
                    self.stats["non_canonical_excluded"] += 1
                    print(f"  [Skipped: Non-self-referencing canonical] Crawled: {final_url} -> Points to: {clean_canonical}")
                    return []
                
                target_url = clean_canonical
            else:
                # Fallback if no canonical tag exists: use the final fetched URL
                target_url = final_url

            # Add to our valid set of canonical sitemap URLs
            if target_url in self.canonical_urls:
                self.stats["duplicates_removed"] += 1
            else:
                self.canonical_urls.add(target_url)

            # 3. Extract standard <a> links for further crawling
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(final_url, href)
                clean_link, _ = urldefrag(full_url)
                clean_link = clean_link.rstrip("/")
                
                parsed_href = urlparse(clean_link)
                if parsed_href.scheme in ('http', 'https') and parsed_href.netloc == self.domain:
                    links.append(clean_link)
            
            return links

        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return []

    def crawl(self, max_pages=3500):
        """Crawls the website up to max_pages safely."""
        print(f"Starting canonical-aware crawl for {self.base_url}...\n")
        
        while self.urls_to_visit and len(self.visited_urls) < max_pages:
            current_url = self.urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            print(f"Crawling ({len(self.visited_urls)+1}): {current_url}")
            self.visited_urls.add(current_url)
            
            new_links = self.process_page(current_url)
            for link in new_links:
                if link not in self.visited_urls and link not in self.urls_to_visit:
                    self.urls_to_visit.append(link)

    def calculate_priority(self, url):
        """Assigns priority based on URL depth."""
        path = urlparse(url).path
        depth = path.count('/')
        
        if depth == 0 or path == "":
            return "1.0" # Homepage
        elif depth == 1:
            return "0.8" # Top-level hubs
        elif depth == 2:
            return "0.6" # Standard district/resource pages
        else:
            return "0.5" # Deep pages

    def generate_xml(self, output_filename="sitemap.xml"):
        """Generates the GSC-compliant XML file and prints the diagnostic summary."""
        print(f"\nGenerating {output_filename}...")
        
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        today = datetime.now().strftime('%Y-%m-%d')

        for url in sorted(self.canonical_urls):
            url_element = ET.SubElement(urlset, "url")
            
            loc = ET.SubElement(url_element, "loc")
            loc.text = url
            
            lastmod = ET.SubElement(url_element, "lastmod")
            lastmod.text = today
            
            priority = ET.SubElement(url_element, "priority")
            priority.text = self.calculate_priority(url)

        tree = ET.ElementTree(urlset)
        ET.indent(tree, space="\t", level=0)
        tree.write(output_filename, encoding="utf-8", xml_declaration=True)
        
        # Print the requested diagnostic report
        print("\n" + "="*40)
        print("          SITEMAP SUMMARY REPORT          ")
        print("="*40)
        print(f"Pages crawled:              {self.stats['crawled']:,}")
        print(f"Non-canonical excluded:     {self.stats['non_canonical_excluded']:,}")
        print(f"Noindex excluded:           {self.stats['noindex_excluded']:,}")
        print(f"External/Non-HTML skipped:  {self.stats['external_or_non_html']:,}")
        print(f"Duplicates removed:         {self.stats['duplicates_removed']:,}")
        print("-" * 40)
        print(f"Final Sitemap URLs:         {len(self.canonical_urls):,}")
        print("="*40)
        print(f"Success! Sitemap saved as {output_filename}.")

if __name__ == "__main__":
    TARGET_URL = "https://www.newyorkspecialed.net" 
    generator = CanonicalSitemapGenerator(TARGET_URL)
    generator.crawl(max_pages=3500) 
    generator.generate_xml("sitemap.xml")