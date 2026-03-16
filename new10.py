import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

class DeepLinkPatcher:
    def __init__(self, site_root):
        self.site_root = site_root
        self.file_index = {}
        
        # Static mapping for orphaned root topics, placeholders, and bad guides
        self.correction_map = {
            # Placeholders
            '/districts/EVALUATION_PROCESS_PAGE_URL': '/guides/evaluation-request-ny/index.html',
            '/districts/GLOSSARY_PAGE_URL': '/districts/nys-overview/index.html',
            '/districts/CSE_MEETING_GUIDE_PAGE_URL': '/guides/cse-meeting-guide/index.html',
            '/districts/ADVOCACY_PAGE_URL': '/guides/parent-advocacy-guide/index.html',
            '/districts/link to iep goals page': '/guides/parent-advocacy-guide/index.html',
            '/districts/link to services and placement page': '/guides/carter-cases-private-placement/index.html',
            '/districts/link to evaluation process page': '/guides/evaluation-request-ny/index.html',
            
            # Orphaned Topics
            '/services': '/districts/nys-overview/index.html',
            '/iep': '/districts/nys-overview/index.html',
            '/accommodations': '/districts/nys-overview/index.html',
            '/evaluation': '/guides/evaluation-request-ny/index.html',
            '/eligibility': '/guides/parent-advocacy-guide/index.html',
            '/iep-goals': '/guides/parent-advocacy-guide/index.html',
            '/disputes': '/guides/dispute-resolution-ny/index.html',
            '/advocacy': '/guides/parent-advocacy-guide/index.html',
            '/cse-meeting': '/guides/cse-meeting-guide/index.html',
            '/rights': '/guides/parent-advocacy-guide/index.html',
            '/dispute-resolution': '/guides/dispute-resolution-ny/index.html',
            '/transition-planning': '/districts/nys-overview/index.html',
            '/cse-meeting-guide': '/guides/cse-meeting-guide/index.html',
            
            # Bad Guide Stubs
            '/guides/glossary': '/districts/nys-overview/index.html',
            '/guides/iep-guide': '/districts/nys-overview/index.html',
            '/guides/service-delivery': '/districts/nys-overview/index.html',
            '/guides/private-school': '/guides/carter-cases-private-placement/index.html',
            '/guides/related-services': '/districts/nys-overview/index.html',
            '/guides/disabilities': '/districts/nys-overview/index.html',
            '/guides/parent-rights': '/guides/parent-advocacy-guide/index.html',
            '/guides/504-plans': '/districts/nys-overview/index.html',
            '/guides/iep-services': '/districts/nys-overview/index.html',
            '/guides/iee': '/guides/evaluation-request-ny/index.html',
            '/guides/special-ed-law': '/guides/parent-advocacy-guide/index.html',
            '/guides/iep-development': '/guides/parent-advocacy-guide/index.html',
            '/guides/transportation': '/districts/nys-overview/index.html',
            
            # Leftover Structural 404s
            '/districts/discipline-rights.html': '/guides/dispute-resolution-ny/index.html',
            '/districts/partners.html': '/about/partners.html',
            '/iep-letter-writer/': '/tools/index.html'
        }

    def index_local_files(self):
        """Builds a lookup table of filename -> absolute path to dynamically fix the Spanish URLs."""
        for root, _, files in os.walk(self.site_root):
            for file in files:
                if file.endswith('.html'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.site_root)
                    web_path = '/' + rel_path.replace(os.sep, '/')
                    self.file_index[file] = web_path
        print(f"Indexed {len(self.file_index)} local HTML files for dynamic routing.")

    def _normalize_href(self, href):
        if not href or href.startswith(('mailto:', 'tel:', '#', 'http')):
            return href
        return unquote(href)

    def fix_html_files(self):
        self.index_local_files()
        files_modified = 0
        links_fixed = 0
        
        for root, _, files in os.walk(self.site_root):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    modified, count = self._process_file(filepath)
                    if modified:
                        files_modified += 1
                        links_fixed += count
                        
        print(f"\nExecution Complete. Modified {files_modified} files and patched {links_fixed} links.")

    def _process_file(self, filepath):
        modified = False
        fix_count = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        anchors = soup.find_all('a', href=True)

        for a_tag in anchors:
            original_href = a_tag['href']
            
            # 1. Fix Relative Link Collapse
            if original_href in ['sachem-csd/', 'greece-csd/', 'east-ramapo-csd/']:
                a_tag['href'] = f"/districts/{original_href.strip('/')}/index.html"
                modified = True
                fix_count += 1
                continue

            normalized_path = self._normalize_href(original_href)
            
            # 2. Fix the broken Spanish architecture dynamically
            if normalized_path and normalized_path.startswith('/districts/'):
                filename = os.path.basename(urlparse(normalized_path).path)
                if filename in self.file_index:
                    a_tag['href'] = self.file_index[filename]
                    modified = True
                    fix_count += 1
                continue

            # 3. Fix static mappings
            if normalized_path in self.correction_map:
                a_tag['href'] = self.correction_map[normalized_path]
                modified = True
                fix_count += 1

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
        return modified, fix_count

if __name__ == "__main__":
    patcher = DeepLinkPatcher(site_root="./")
    patcher.fix_html_files()