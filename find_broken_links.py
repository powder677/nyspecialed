#!/usr/bin/env python3
"""
Find and fix broken href links in HTML files
Looks for malformed patterns like: href="/districts/weatherford-isd/a>
"""

import sys
from pathlib import Path
import re

def find_broken_links(file_path):
    """Find broken href links in a file."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to find broken hrefs like: href="/districts/DISTRICT/a>
        # or href="/districts/DISTRICT/a></li>
        broken_pattern = re.compile(
            r'href="([^"]*?/a>)',
            re.IGNORECASE
        )
        
        matches = broken_pattern.findall(content)
        
        if matches:
            return matches
        return None
            
    except Exception as e:
        return None


def preview_broken_links(base_path):
    """Preview files with broken links."""
    
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"❌ Error: {base_path} does not exist")
        return
    
    # Find all HTML files
    html_files = list(base_path.rglob('*.html'))
    
    if not html_files:
        print(f"❌ No HTML files found in {base_path}")
        return
    
    print(f"🔍 Scanning {len(html_files)} HTML files for broken links...")
    print("=" * 70)
    
    broken_files = []
    
    for html_file in html_files:
        broken = find_broken_links(html_file)
        if broken:
            broken_files.append({
                'file': html_file,
                'broken_links': broken
            })
    
    if not broken_files:
        print("✓ No broken links found!")
        return
    
    print(f"\n⚠️  Found broken links in {len(broken_files)} files:\n")
    
    for item in broken_files[:20]:  # Show first 20
        print(f"📄 {item['file']}")
        for link in item['broken_links'][:3]:  # Show first 3 broken links per file
            print(f"   ✗ href=\"{link}\"")
        if len(item['broken_links']) > 3:
            print(f"   ... and {len(item['broken_links']) - 3} more broken links")
        print()
    
    if len(broken_files) > 20:
        print(f"... and {len(broken_files) - 20} more files with broken links\n")
    
    print("=" * 70)
    print(f"\nTotal files with broken links: {len(broken_files)}")
    
    # Ask if user wants to see the fix script
    print("\nWould you like me to show you what the broken HTML looks like")
    print("with more context? This will help determine the best fix. (y/n): ", end='')
    
    response = input().strip().lower()
    
    if response == 'y':
        show_context(broken_files[:5])


def show_context(broken_files):
    """Show broken links with surrounding HTML context."""
    
    print("\n" + "=" * 70)
    print("BROKEN LINKS WITH CONTEXT")
    print("=" * 70 + "\n")
    
    for item in broken_files:
        print(f"📄 File: {item['file']}\n")
        
        try:
            with open(item['file'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find each broken link and show 100 chars before and after
            for broken_link in item['broken_links'][:2]:
                pattern = re.escape(f'href="{broken_link}"')
                match = re.search(pattern, content)
                if match:
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end]
                    
                    print(f"Broken: href=\"{broken_link}\"")
                    print(f"Context: ...{context}...")
                    print()
            
            print("-" * 70 + "\n")
        except:
            pass


def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("FIND BROKEN HREF LINKS")
        print("=" * 70)
        print("\nUsage:")
        print("  python find_broken_links.py <directory>")
        print("\nExamples:")
        print("  python find_broken_links.py districts")
        print("\nThis finds broken patterns like:")
        print('  href="/districts/weatherford-isd/a>')
        print('  href="/districts/weslaco-isd/a></li>')
        print("=" * 70)
        sys.exit(1)
    
    base_path = sys.argv[1]
    preview_broken_links(base_path)


if __name__ == '__main__':
    main()