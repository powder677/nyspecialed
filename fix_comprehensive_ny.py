#!/usr/bin/env python3
"""
Comprehensive fix for ALL remaining New York Special Ed 404 errors
This addresses the ACTUAL problems causing 404s
"""

import sys
from pathlib import Path
import re

def fix_comprehensive(file_path):
    """Fix all remaining link issues in a file."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # ===== CRITICAL FIX 1: TRAILING SLASHES =====
        # These cause 404s because files are .html not directories
        # Fix: page/ → page.html
        
        trailing_slash_fixes = [
            ('href="cse-meeting-guide/"', 'href="cse-meeting-guide.html"'),
            ('href="discipline-rights/"', 'href="discipline-rights.html"'),
            ('href="evaluation-process/"', 'href="evaluation-process.html"'),
            ('href="parent-advocacy-guide/"', 'href="parent-advocacy-guide.html"'),
            ('href="special-ed-updates/"', 'href="special-ed-updates.html"'),
            ('href="leadership-directory/"', 'href="leadership-directory.html"'),
            ('href="partners/"', 'href="partners.html"'),
        ]
        
        for old, new in trailing_slash_fixes:
            if old in content:
                content = content.replace(old, new)
                changes.append('trailing-slash')
        
        # ===== FIX 2: MISSING .html EXTENSIONS =====
        # Some links are missing .html entirely
        
        missing_html_patterns = [
            (r'href="partners"([^a-zA-Z])', r'href="partners.html"\1'),
            (r'href="cse-meeting-guide"([^a-zA-Z])', r'href="cse-meeting-guide.html"\1'),
        ]
        
        for pattern, replacement in missing_html_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes.append('missing-html')
        
        # ===== FIX 3: CASE SENSITIVITY ISSUES =====
        # Files are lowercase but links have capitals
        
        case_fixes = [
            ('href="CSE-Meeting-Guide"', 'href="cse-meeting-guide.html"'),
            ('href="IEP-Guide"', 'href="/guides/iep-guide/"'),
            ('href="IEPGuide.html"', 'href="/guides/iep-guide/"'),
            ('href="Dispute-Resolution"', 'href="discipline-rights.html"'),
            ('href="DisputeResolution.html"', 'href="discipline-rights.html"'),
            ('href="Evaluation-Process"', 'href="evaluation-process.html"'),
        ]
        
        for old, new in case_fixes:
            if old in content:
                content = content.replace(old, new)
                changes.append('case-fix')
        
        # ===== FIX 4: ALL REMAINING PLACEHOLDER VARIATIONS =====
        
        # Format: replace/with/xxx
        placeholder_patterns_1 = {
            'replace/with/cse/meeting/page/url': 'cse-meeting-guide.html',
            'replace/with/evaluation/page/url': 'evaluation-process.html',
            'replace/with/advocacy/page/url': 'parent-advocacy-guide.html',
            'replace/with/iep/page/url': '/guides/iep-guide/',
            'replace/with/dispute/resolution/page/url': 'discipline-rights.html',
            'replace/with/law/page/url': '/guides/special-ed-law/',
        }
        
        for placeholder, actual in placeholder_patterns_1.items():
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append('placeholder-1')
        
        # Format: UPPERCASE WITH SPACES (check both regular and URL-encoded %20)
        placeholder_patterns_2 = {
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
        
        for placeholder, actual in placeholder_patterns_2.items():
            # Check both versions
            for version in [placeholder, placeholder.replace(' ', '%20')]:
                pattern = f'href="{version}"'
                replacement = f'href="{actual}"'
                if pattern in content:
                    content = content.replace(pattern, replacement)
                    changes.append('placeholder-2')
        
        # Format: lowercase-with-hyphens
        placeholder_patterns_3 = {
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
            'link to disagreements page': 'discipline-rights.html',
        }
        
        for placeholder, actual in placeholder_patterns_3.items():
            # Check both regular and URL-encoded
            for version in [placeholder, placeholder.replace(' ', '%20')]:
                pattern = f'href="{version}"'
                replacement = f'href="{actual}"'
                if pattern in content:
                    content = content.replace(pattern, replacement)
                    changes.append('placeholder-3')
        
        # Format: [INSERT LINK ...]
        placeholder_patterns_4 = {
            '[INSERT LINK TO CSE MEETING GUIDE PAGE HERE]': 'cse-meeting-guide.html',
            '[INSERT LINK TO DISPUTE RESOLUTION PAGE HERE]': 'discipline-rights.html',
            '[INSERT LINK TO EVALUATION PROCESS PAGE HERE]': 'evaluation-process.html',
            '[INSERT LINK TO IEP GOALS PAGE HERE]': '/guides/iep-goals/',
            '[INSERT LINK TO PARENT RIGHTS PAGE HERE]': '/guides/parent-rights/',
            '[INSERT LINK TO SPECIAL EDUCATION SERVICES PAGE HERE]': '/guides/services/',
        }
        
        for placeholder, actual in placeholder_patterns_4.items():
            for version in [placeholder, placeholder.replace(' ', '%20')]:
                pattern = f'href="{version}"'
                replacement = f'href="{actual}"'
                if pattern in content:
                    content = content.replace(pattern, replacement)
                    changes.append('placeholder-4')
        
        # Format: replace-with-xxx-url
        placeholder_patterns_5 = {
            'replace-with-cse-meeting-guide-url': 'cse-meeting-guide.html',
            'replace-with-disputes-page-url': 'discipline-rights.html',
            'replace-with-eligibility-page-url': '/guides/eligibility/',
            'replace-with-evaluation-page-url': 'evaluation-process.html',
            'replace-with-iep-development-page-url': '/guides/iep-development/',
            'replace-with-parent-rights-page-url': '/guides/parent-rights/',
            'replace-with-services-page-url': '/guides/services/',
        }
        
        for placeholder, actual in placeholder_patterns_5.items():
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append('placeholder-5')
        
        # Format: Special cases and typos
        special_cases = {
            'DISPUTE_RESOLUTION_PAGE_URL': 'discipline-rights.html',
            'IEP_PAGE_URL': '/guides/iep-guide/',
            'All-About-IEPs': '/guides/iep-guide/',
            'Evaluation-Process': 'evaluation-process.html',
            'iepservices': '/guides/iep-services/',
            'evaluation': 'evaluation-process.html',
            'disputes': 'discipline-rights.html',
            'services': '/guides/services/',
            'iep': '/guides/iep-guide/',
        }
        
        for placeholder, actual in special_cases.items():
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes.append('special-case')
        
        # ===== FIX 5: SPANISH PAGE LINKS =====
        # Spanish pages linking to English pages that don't exist in Spanish
        # Example: /districts/.../evaluation-process.html doesn't exist
        # Fix: Link to English version or remove
        
        # Pattern: href="evaluation-process.html" in Spanish files
        # Check if this is a Spanish file
        file_str = str(file_path)
        if '/es/' in file_str or '\\es\\' in file_str or file_str.endswith('-es.html'):
            # This is a Spanish file
            # Remove broken Spanish subpage links - they link back to main district page
            spanish_broken_links = [
                'evaluation-process.html',
                'cse-meeting-guide.html',
                'discipline-rights.html',
            ]
            
            for broken_link in spanish_broken_links:
                pattern = f'href="{broken_link}"'
                # Link to parent directory (district main page) instead
                replacement = 'href="../"'
                if pattern in content:
                    content = content.replace(pattern, replacement)
                    changes.append('spanish-fix')
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Fixed {len(set(changes))} issue types"
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
    
    print(f"🔧 Found {len(html_files)} HTML files to process")
    print("=" * 70)
    
    updated = 0
    skipped = 0
    errors = 0
    
    for html_file in html_files:
        success, message = fix_comprehensive(html_file)
        
        if success:
            updated += 1
            # Show first 100
            if updated <= 100:
                print(f"✓ {html_file.name}: {message}")
            elif updated == 101:
                print("... (showing first 100 updates)")
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
    
    if updated > 0:
        print("\n🎉 Changes made! This should fix the remaining 291 404 errors.")
    else:
        print("\n⚠️  No files updated. The 404s may be caused by:")
        print("   1. Missing pages that need to be created")
        print("   2. Server-side redirect issues")
        print("   3. Links in pages not in this directory")


def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("COMPREHENSIVE FIX - All Remaining 404 Errors")
        print("=" * 70)
        print("\nUsage:")
        print("  python fix_comprehensive_ny.py <directory>")
        print("\nExamples:")
        print("  python fix_comprehensive_ny.py \\Users\\elisa\\OneDrive\\Documents\\github\\nyspecialed")
        print("\nThis fixes:")
        print("  • Trailing slashes (page/ → page.html)")
        print("  • Missing .html extensions")
        print("  • Case sensitivity issues")
        print("  • ALL placeholder URL variations")
        print("  • Spanish page link issues")
        print("\nShould eliminate the remaining 291 404 errors!")
        print("=" * 70)
        sys.exit(1)
    
    base_path = sys.argv[1]
    process_directory(base_path)


if __name__ == '__main__':
    main()