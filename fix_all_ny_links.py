#!/usr/bin/env python3
"""
Fix ALL placeholder URLs and trailing slash issues in New York Special Ed site
Addresses ~600 broken links found by Ahrefs
"""

import sys
from pathlib import Path
import re

def fix_all_issues(file_path):
    """Fix both placeholder URLs and trailing slash issues in a file."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # ===== FIX 1: TRAILING SLASH ISSUES =====
        # Links like href="cse-meeting-guide/" should be href="cse-meeting-guide.html"
        
        pages = [
            'cse-meeting-guide',
            'discipline-rights',
            'evaluation-process',
            'parent-advocacy-guide',
            'special-ed-updates',
            'leadership-directory',
            'partners'
        ]
        
        for page in pages:
            # Fix: href="page/" → href="page.html"
            pattern = f'href="{page}/"'
            replacement = f'href="{page}.html"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append(f"trailing-slash:{page}")
        
        # ===== FIX 2: PLACEHOLDER URLs - Multiple formats =====
        
        # Format 1: replace/with/xxx/page/url
        replacements = {
            'replace/with/cse/meeting/page/url': 'cse-meeting-guide.html',
            'replace/with/evaluation/page/url': 'evaluation-process.html',
            'replace/with/advocacy/page/url': 'parent-advocacy-guide.html',
            'replace/with/iep/page/url': '/guides/iep-guide/',
            'replace/with/dispute/resolution/page/url': 'discipline-rights.html',
            'replace/with/law/page/url': '/guides/special-ed-law/',
        }
        
        for placeholder, actual_url in replacements.items():
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual_url}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append(f"placeholder:{placeholder}")
        
        # Format 2: LINK TO XXX PAGE (with spaces, URL encoded as %20)
        link_to_patterns = {
            'LINK TO ADVOCACY TIPS PAGE': 'parent-advocacy-guide.html',
            'LINK TO ADVOCACY PAGE': 'parent-advocacy-guide.html',
            'LINK TO CSE MEETING GUIDE PAGE': 'cse-meeting-guide.html',
            'LINK TO CSE MEETING GUIDE': 'cse-meeting-guide.html',
            'LINK TO EVALUATION PROCESS PAGE': 'evaluation-process.html',
            'LINK TO PLACEMENT OPTIONS PAGE': '/guides/placement-options/',
            'LINK TO RESOURCES AND SUPPORT PAGE': 'partners.html',
            'LINK TO UNDERSTANDING IEPS PAGE': '/guides/iep-guide/',
            'LINK TO IEP DEVELOPMENT PAGE': '/guides/iep-development/',
            'LINK TO IEP GUIDE PAGE': '/guides/iep-guide/',
            'LINK TO IEP GOALS PAGE': '/guides/iep-goals/',
            'LINK TO IEP GOALS 101 PAGE': '/guides/iep-goals/',
            'LINK TO SERVICES PAGE': '/guides/services/',
            'LINK TO RELATED SERVICES PAGE': '/guides/related-services/',
            'LINK TO SPECIAL EDUCATION SERVICES PAGE': '/guides/services/',
            'LINK TO SERVICE DELIVERY PAGE': '/guides/service-delivery/',
            'LINK TO DISABILITIES PAGE': '/guides/disabilities/',
            'LINK TO COMMUNITY RESOURCES PAGE': 'partners.html',
            'LINK TO GLOSSARY PAGE': '/guides/glossary/',
            'LINK TO PRIVATE SCHOOL PAGE': '/guides/private-school/',
            'LINK TO TRANSPORTATION PAGE': '/guides/transportation/',
            'LINK TO NY PARENT RIGHTS PAGE': '/guides/parent-rights/',
        }
        
        for placeholder, actual_url in link_to_patterns.items():
            # Check both regular and URL-encoded versions
            encoded = placeholder.replace(' ', '%20')
            for version in [placeholder, encoded]:
                pattern = f'href="{version}"'
                replacement = f'href="{actual_url}"'
                if pattern in content:
                    content = content.replace(pattern, replacement)
                    changes.append(f"LINK-TO:{placeholder}")
        
        # Format 3: link-to-xxx-page (lowercase with hyphens)
        link_hyphen_patterns = {
            'link-to-cse-meeting-page': 'cse-meeting-guide.html',
            'link-to-evaluation-page': 'evaluation-process.html',
            'link-to-advocacy-page': 'parent-advocacy-guide.html',
            'link-to-iep-page': '/guides/iep-guide/',
            'link-to-dispute-resolution-page': 'discipline-rights.html',
            'link-to-glossary-page': '/guides/glossary/',
            'link-to-resources-page': 'partners.html',
            'link-to-504-plans-page': '/guides/504-plans/',
            'link-to-iee-page': '/guides/iee/',
            'link-to-iep-disagreements-page': 'discipline-rights.html',
            'link-to-parent-rights-page': '/guides/parent-rights/',
            'link-to-iep-development-page': '/guides/iep-development/',
            'link-to-service-delivery-page': '/guides/service-delivery/',
           'link-to-eligibility-page': '/guides/eligibility/',
        }
        
        for placeholder, actual_url in link_hyphen_patterns.items():
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual_url}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append(f"link-to:{placeholder}")
        
        # Format 4: [INSERT LINK TO XXX PAGE HERE]
        insert_patterns = {
            '[INSERT LINK TO CSE MEETING GUIDE PAGE HERE]': 'cse-meeting-guide.html',
            '[INSERT LINK TO DISPUTE RESOLUTION PAGE HERE]': 'discipline-rights.html',
            '[INSERT LINK TO EVALUATION PROCESS PAGE HERE]': 'evaluation-process.html',
            '[INSERT LINK TO IEP GOALS PAGE HERE]': '/guides/iep-goals/',
            '[INSERT LINK TO PARENT RIGHTS PAGE HERE]': '/guides/parent-rights/',
            '[INSERT LINK TO SPECIAL EDUCATION SERVICES PAGE HERE]': '/guides/services/',
        }
        
        for placeholder, actual_url in insert_patterns.items():
            # Check both regular and URL-encoded versions
            encoded = placeholder.replace(' ', '%20')
            for version in [placeholder, encoded]:
                pattern = f'href="{version}"'
                replacement = f'href="{actual_url}"'
                if pattern in content:
                    content = content.replace(pattern, replacement)
                    changes.append(f"INSERT:{placeholder}")
        
        # Format 5: replace-with-xxx-url (with hyphens)
        replace_hyphen_patterns = {
            'replace-with-cse-meeting-guide-url': 'cse-meeting-guide.html',
            'replace-with-disputes-page-url': 'discipline-rights.html',
            'replace-with-eligibility-page-url': '/guides/eligibility/',
            'replace-with-evaluation-page-url': 'evaluation-process.html',
            'replace-with-iep-development-page-url': '/guides/iep-development/',
            'replace-with-parent-rights-page-url': '/guides/parent-rights/',
            'replace-with-services-page-url': '/guides/services/',
        }
        
        for placeholder, actual_url in replace_hyphen_patterns.items():
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual_url}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append(f"replace-with:{placeholder}")
        
        # Format 6: Other special cases
        special_cases = {
            'DISPUTE_RESOLUTION_PAGE_URL': 'discipline-rights.html',
            'All-About-IEPs': '/guides/iep-guide/',
            'Evaluation-Process': 'evaluation-process.html',
            'iepservices': '/guides/iep-services/',
        }
        
        for placeholder, actual_url in special_cases.items():
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual_url}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append(f"special:{placeholder}")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Fixed {len(changes)} issues: {', '.join(set(changes[:5]))}"
        else:
            return False, "No issues found"
            
    except Exception as e:
        return False, f"Error: {str(e)}"


def process_directory(base_path):
    """Process all HTML files in directory."""
    
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"❌ Error: {base_path} does not exist")
        return
    
    # Find all HTML files
    html_files = list(base_path.rglob('*.html'))
    
    if not html_files:
        print(f"❌ No HTML files found in {base_path}")
        return
    
    print(f"🔧 Found {len(html_files)} HTML files to check")
    print("=" * 70)
    
    updated = 0
    skipped = 0
    errors = 0
    
    for html_file in html_files:
        success, message = fix_all_issues(html_file)
        
        if success:
            updated += 1
            # Show first 100
            if updated <= 100:
                print(f"✓ {html_file.name}: {message}")
        else:
            if "Error" in message:
                errors += 1
                if errors <= 10:
                    print(f"✗ {html_file.name}: {message}")
            else:
                skipped += 1
    
    print("=" * 70)
    print(f"\n✓ Files updated: {updated}")
    print(f"○ Skipped (no issues): {skipped}")
    if errors > 0:
        print(f"✗ Errors: {errors}")
    print("\nDone! This should fix most of the ~600 broken links in Ahrefs.")


def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("FIX ALL BROKEN LINKS - New York Special Ed Site")
        print("=" * 70)
        print("\nUsage:")
        print("  python fix_all_ny_links.py <directory>")
        print("\nExamples:")
        print("  python fix_all_ny_links.py districts")
        print("  python fix_all_ny_links.py \\Users\\elisa\\OneDrive\\Documents\\github\\nyspecialed")
        print("\nThis fixes:")
        print("  1. Placeholder URLs (replace/with/..., LINK TO ..., etc.)")
        print("  2. Trailing slash issues (page/ → page.html)")
        print("\nShould eliminate ~600 broken links from Ahrefs!")
        print("=" * 70)
        sys.exit(1)
    
    base_path = sys.argv[1]
    process_directory(base_path)


if __name__ == '__main__':
    main()