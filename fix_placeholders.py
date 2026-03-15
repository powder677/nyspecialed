#!/usr/bin/env python3
"""
Fix placeholder URLs in New York Special Ed HTML files
Replaces "replace/with/..." URLs with actual page URLs
"""

import sys
from pathlib import Path
import re

# Mapping of placeholder URLs to actual URLs
URL_MAPPINGS = {
    'replace/with/cse/meeting/page/url': 'cse-meeting-guide.html',
    'replace/with/evaluation/page/url': 'evaluation-process.html',
    'replace/with/advocacy/page/url': 'parent-advocacy-guide.html',
    'replace/with/iep/page/url': '/guides/iep-guide/',  # Adjust to your actual IEP guide URL
    'replace/with/dispute/resolution/page/url': 'discipline-rights.html',  # or your dispute resolution page
    'replace/with/law/page/url': '/guides/special-ed-law/',  # Adjust to your actual law page URL
}

def fix_placeholder_urls(file_path):
    """Fix placeholder URLs in a single file."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = 0
        
        # Replace each placeholder URL with its actual URL
        for placeholder, actual_url in URL_MAPPINGS.items():
            # Create pattern to match href="placeholder"
            pattern = f'href="{placeholder}"'
            replacement = f'href="{actual_url}"'
            
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes += content.count(replacement) - original_content.count(replacement)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Fixed {changes} placeholder URLs"
        else:
            return False, "No placeholders found"
            
    except Exception as e:
        return False, f"Error: {str(e)}"


def preview_placeholders(base_path):
    """Preview placeholder URLs before fixing."""
    
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"❌ Error: {base_path} does not exist")
        return None
    
    # Find all HTML files
    html_files = list(base_path.rglob('*.html'))
    
    if not html_files:
        print(f"❌ No HTML files found in {base_path}")
        return None
    
    print(f"🔍 Scanning {len(html_files)} HTML files for placeholder URLs...")
    print("=" * 70)
    
    files_with_placeholders = []
    placeholder_counts = {p: 0 for p in URL_MAPPINGS.keys()}
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_placeholders = []
            for placeholder in URL_MAPPINGS.keys():
                count = content.count(f'href="{placeholder}"')
                if count > 0:
                    file_placeholders.append((placeholder, count))
                    placeholder_counts[placeholder] += count
            
            if file_placeholders:
                files_with_placeholders.append({
                    'file': html_file,
                    'placeholders': file_placeholders
                })
        except:
            pass
    
    if not files_with_placeholders:
        print("✓ No placeholder URLs found!")
        return None
    
    print(f"\n⚠️  Found placeholder URLs in {len(files_with_placeholders)} files:\n")
    
    for item in files_with_placeholders[:10]:
        print(f"📄 {item['file'].name}:")
        for placeholder, count in item['placeholders']:
            actual_url = URL_MAPPINGS[placeholder]
            print(f"   • {placeholder}")
            print(f"     → Will become: {actual_url} ({count} occurrences)")
        print()
    
    if len(files_with_placeholders) > 10:
        print(f"... and {len(files_with_placeholders) - 10} more files\n")
    
    print("=" * 70)
    print(f"\nTotal placeholder URLs by type:")
    for placeholder, count in placeholder_counts.items():
        if count > 0:
            print(f"  • {placeholder}: {count} occurrences")
            print(f"    → {URL_MAPPINGS[placeholder]}")
    
    return files_with_placeholders


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
    total_fixes = 0
    
    for html_file in html_files:
        success, message = fix_placeholder_urls(html_file)
        
        if success:
            updated += 1
            # Extract number of fixes
            if "Fixed" in message:
                num = int(message.split()[1])
                total_fixes += num
            
            # Show first 50
            if updated <= 50:
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
    print(f"✓ Total placeholder URLs fixed: {total_fixes}")
    print(f"○ Skipped (no placeholders): {skipped}")
    if errors > 0:
        print(f"✗ Errors: {errors}")
    print("\nDone!")


def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("FIX PLACEHOLDER URLs - New York Special Ed Site")
        print("=" * 70)
        print("\nUsage:")
        print("  python fix_placeholders.py <directory> [--preview]")
        print("\nExamples:")
        print("  python fix_placeholders.py districts --preview")
        print("  python fix_placeholders.py districts")
        print("\nThis fixes placeholder patterns like:")
        print('  href="replace/with/cse/meeting/page/url"')
        print('  → href="cse-meeting-guide.html"')
        print("\n⚠️  Edit the URL_MAPPINGS in the script to customize replacements!")
        print("=" * 70)
        sys.exit(1)
    
    base_path = sys.argv[1]
    preview_mode = '--preview' in sys.argv
    
    if preview_mode:
        preview_placeholders(base_path)
    else:
        process_directory(base_path)


if __name__ == '__main__':
    main()