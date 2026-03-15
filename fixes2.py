import os
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

class BrokenLinkPatcher:
    def __init__(self, site_root):
        self.site_root = site_root
        
        # Explicit mapping mapping broken 404s (from your Ahrefs CSV) to existing canonical files
        # We strip the domain to easily match both absolute and relative hrefs
        self.correction_map = {
            '/districts/evaluation-process.html': '/guides/evaluation-request-ny/index.html',
            '/districts/cse-meeting-guide.html': '/guides/cse-meeting-guide/index.html',
            '/districts/CSEMeetingGuide.html': '/guides/cse-meeting-guide/index.html',
            '/districts/Placement-Options': '/guides/carter-cases-private-placement/index.html',
            '/districts/ServicesAndPlacement.html': '/guides/carter-cases-private-placement/index.html',
            '/guides/eligibility': '/guides/parent-advocacy-guide/index.html',
            '/guides/glossary': '/districts/nys-overview/index.html', # Fallback mapping
            '/related-services': '/districts/nys-overview/index.html',
            '/evaluation-process': '/guides/evaluation-request-ny/index.html',
            '/mandated-services': '/districts/nys-overview/index.html',
            '/placement-options': '/guides/carter-cases-private-placement/index.html',
            '/districts/link to cse meeting guide page': '/guides/cse-meeting-guide/index.html'
        }

    def _normalize_href(self, href):
        """Extracts the path from an href to match against our correction map."""
        if not href or href.startswith(('mailto:', 'tel:', '#')):
            return None
        
        # Decode URL encoded characters (e.g., %20 to space)
        href = unquote(href)
        
        parsed = urlparse(href)
        path = parsed.path
        
        # Ensure it starts with a slash for consistent dictionary matching
        if not path.startswith('/'):
            path = '/' + path
            
        return path

    def fix_html_files(self):
        """Recursively scans HTML files and updates broken links in-place."""
        print(f"Scanning repository at: {self.site_root}")
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
                        
        print(f"\nExecution Complete.")
        print(f"Files Modified: {files_modified}")
        print(f"Total Links Patched: {links_fixed}")

    def _process_file(self, filepath):
        """Parses an HTML file, patches hrefs, and overwrites if changes occurred."""
        modified = False
        fix_count = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        anchors = soup.find_all('a', href=True)

        for a_tag in anchors:
            original_href = a_tag['href']
            normalized_path = self._normalize_href(original_href)
            
            if normalized_path in self.correction_map:
                new_url = self.correction_map[normalized_path]
                a_tag['href'] = new_url
                modified = True
                fix_count += 1
                # print(f"Fixed: {original_href} -> {new_url} in {filepath}")

        # specific catch for the Spanish 404 identified in the Ahrefs snippet
        for a_tag in anchors:
            if 'que-es-un-iep-washington-heights.html' in a_tag['href'] and '/es/' in a_tag['href']:
                a_tag['href'] = '/districts/nyc-district-06-washington-heights/que-es-un-iep-washington-heights.html'
                modified = True
                fix_count += 1

        if modified:
            # Save the fixed HTML back to the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
        return modified, fix_count

if __name__ == "__main__":
    # Point this to your local nyspecialed repository directory
    repo_directory = "./" 
    patcher = BrokenLinkPatcher(site_root=repo_directory)
    patcher.fix_html_files()