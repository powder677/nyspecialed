#!/usr/bin/env python3
"""
Broken Link Fixer - Repairs broken links identified in link audit report
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


class BrokenLinkFixer:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.fixes_applied = 0
        self.errors = []
        
    def parse_report(self, report_path: str) -> List[Dict]:
        """Parse the link audit report to extract broken links"""
        broken_links = []
        
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract unfixable links section
        unfixable_section = re.search(
            r'=== UNFIXABLE / STILL BROKEN ===(.*?)(?:===|$)', 
            content, 
            re.DOTALL
        )
        
        if not unfixable_section:
            print("No unfixable links found in report")
            return broken_links
        
        # Pattern to match broken link entries
        pattern = r'UNFIXABLE \(Missing Target\) in (.*?): \[(.*?)\] -> \[(.*?)\]'
        
        matches = re.findall(pattern, unfixable_section.group(1))
        
        for file_path, link_text, target in matches:
            broken_links.append({
                'file': file_path.replace('.\\', '').replace('\\', '/'),
                'link_text': link_text,
                'target': target
            })
        
        return broken_links
    
    def suggest_fix(self, link_text: str, target: str) -> str:
        """Suggest a corrected link based on patterns"""
        
        # Common fix patterns
        fixes = {
            # Guides that should point to index.html
            'Community-Resources/': '/guides/index.html',
            'Special-Education-Services/': '/guides/index.html',
            'Parent-Rights-in-Special-Education/': '/guides/parent-advocacy-guide/index.html',
            'Placement-Options/': '/guides/index.html',
            'IEP-Process/': '/guides/index.html',
            'Advocacy-Tips/': '/guides/parent-advocacy-guide/index.html',
            'Transition-Planning/': '/guides/index.html',
            'Glossary/': '/guides/index.html',
            'resources/': '/guides/index.html',
            
            # Specific guide references
            '/guides/eligibility/': '/guides/index.html',
            '/guides/related-services/': '/guides/index.html',
            '/guides/glossary/': '/guides/index.html',
            '/guides/iep-goals/': '/guides/index.html',
            '/guides/service-delivery/': '/guides/index.html',
            '/guides/transportation/': '/guides/index.html',
            '/guides/private-school/': '/guides/index.html',
            '/guides/disabilities/': '/guides/index.html',
            
            # District-specific paths - map to parent directory
            '/districts/nys-overview/parent-advocacy-guide/': '/guides/parent-advocacy-guide/index.html',
            '/districts/nys-overview/leadership-directory/': '/districts/nys-overview/index.html',
            '/districts/nys-overview/evaluation-process/': '/guides/evaluation-request-ny/index.html',
            '/districts/nys-overview/discipline-rights/': '/districts/nys-overview/index.html',
            '/districts/nys-overview/special-ed-updates/': '/districts/nys-overview/index.html',
            '/districts/patchogue-medford-ufsd/evaluation-process/': '/guides/evaluation-request-ny/index.html',
        }
        
        # Check for exact match
        if link_text in fixes:
            return fixes[link_text]
        
        # Check for partial matches
        for pattern, fix in fixes.items():
            if pattern in link_text:
                return fix
        
        # Malformed links with "link to" text
        if 'link to' in link_text.lower():
            if 'evaluation' in link_text.lower():
                return '/guides/evaluation-request-ny/index.html'
            elif 'cse meeting' in link_text.lower():
                return '/guides/cse-meeting-guide/index.html'
            elif 'iep goals' in link_text.lower():
                return '/guides/index.html'
            elif 'services' in link_text.lower():
                return '/guides/index.html'
            elif 'resources' in link_text.lower():
                return '/guides/index.html'
        
        # Default fallback to guides index
        return '/guides/index.html'
    
    def fix_links_in_file(self, file_path: str, link_text: str, old_target: str, new_target: str, dry_run: bool = True) -> bool:
        """Fix a specific link in an HTML file"""
        
        full_path = self.base_dir / file_path
        
        if not full_path.exists():
            self.errors.append(f"File not found: {full_path}")
            return False
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try multiple patterns to match the link
            patterns = [
                f'href="{link_text}"',
                f"href='{link_text}'",
                f'href="{old_target}"',
                f"href='{old_target}'",
            ]
            
            found = False
            new_content = content
            
            for pattern in patterns:
                if pattern in content:
                    replacement = f'href="{new_target}"'
                    new_content = new_content.replace(pattern, replacement)
                    found = True
                    break
            
            if not found:
                self.errors.append(f"Link pattern not found in {file_path}")
                return False
            
            if not dry_run:
                # Backup original file
                backup_path = full_path.with_suffix('.html.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Write fixed content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.fixes_applied += 1
                return True
            else:
                return True
                
        except Exception as e:
            self.errors.append(f"Error processing {file_path}: {str(e)}")
            return False
    
    def generate_fix_mapping(self, broken_links: List[Dict], output_file: str = "link_fixes_mapping.txt"):
        """Generate a human-readable mapping file for review"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PROPOSED LINK FIXES - REVIEW BEFORE APPLYING\n")
            f.write("=" * 80 + "\n\n")
            
            for item in broken_links:
                suggested = self.suggest_fix(item['link_text'], item['target'])
                f.write(f"File: {item['file']}\n")
                f.write(f"  Broken Link: [{item['link_text']}] -> [{item['target']}]\n")
                f.write(f"  Suggested Fix: {suggested}\n")
                f.write("-" * 80 + "\n")
        
        print(f"\n✓ Generated fix mapping: {output_file}")
        print("Review this file and edit suggestions before applying fixes.")
    
    def apply_fixes(self, broken_links: List[Dict], dry_run: bool = True):
        """Apply fixes to all broken links"""
        
        print(f"\n{'DRY RUN - ' if dry_run else ''}Fixing {len(broken_links)} broken links...\n")
        
        for item in broken_links:
            suggested = self.suggest_fix(item['link_text'], item['target'])
            
            success = self.fix_links_in_file(
                item['file'],
                item['link_text'],
                item['target'],
                suggested,
                dry_run
            )
            
            if success:
                status = "✓" if not dry_run else "→"
                print(f"{status} {item['file']}")
                print(f"  {item['link_text']} => {suggested}")
            else:
                print(f"✗ Failed: {item['file']}")
        
        if dry_run:
            print(f"\n{len(broken_links)} links would be fixed")
            print("Run with --apply to make actual changes")
        else:
            print(f"\n✓ Successfully fixed {self.fixes_applied} links")
            print(f"✗ {len(self.errors)} errors occurred")
            
            if self.errors:
                print("\nErrors:")
                for error in self.errors:
                    print(f"  - {error}")


def main():
    parser = argparse.ArgumentParser(
        description='Fix broken links from link audit report'
    )
    parser.add_argument(
        'report',
        help='Path to link audit report file'
    )
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory containing HTML files (default: current directory)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply fixes (default: dry run only)'
    )
    parser.add_argument(
        '--generate-mapping',
        action='store_true',
        help='Generate a mapping file for manual review'
    )
    
    args = parser.parse_args()
    
    fixer = BrokenLinkFixer(args.base_dir)
    
    print("Parsing link audit report...")
    broken_links = fixer.parse_report(args.report)
    
    print(f"Found {len(broken_links)} broken links to fix")
    
    if args.generate_mapping:
        fixer.generate_fix_mapping(broken_links)
    
    if args.apply or not args.generate_mapping:
        fixer.apply_fixes(broken_links, dry_run=not args.apply)


if __name__ == '__main__':
    main()