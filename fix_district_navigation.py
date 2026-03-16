#!/usr/bin/env python3
"""
Fix district navigation menus - update links to point to /guides/ when local pages don't exist
"""

from pathlib import Path
import re
from typing import Dict, List


class NavigationFixer:
    """Fixes district navigation menus by updating broken relative links"""
    
    # Mapping of local page names to guide equivalents
    PAGE_MAPPINGS = {
        'cse-meeting-guide.html': '/guides/cse-meeting-guide/index.html',
        'evaluation-process.html': '/guides/evaluation-request-ny/index.html',
        'discipline-rights.html': '/guides/index.html',
        'leadership-directory.html': '/guides/index.html',
        'special-ed-updates.html': '/guides/index.html',
        'partners.html': '/guides/index.html',
        'parent-advocacy-guide.html': '/guides/parent-advocacy-guide/index.html'
    }
    
    def __init__(self, base_dir: str = '.'):
        self.base_dir = Path(base_dir)
        self.fixes_applied = 0
        
    def find_navigation_blocks(self, html_path: Path) -> List[str]:
        """Find navigation blocks in HTML file"""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to find the navigation block
        nav_pattern = r'<a href="cse-meeting-guide\.html">.*?</a>'
        matches = re.findall(nav_pattern, content, re.DOTALL)
        return matches
    
    def check_local_pages_exist(self, html_path: Path) -> Dict[str, bool]:
        """Check which navigation pages exist in the same directory"""
        directory = html_path.parent
        existence = {}
        
        for page_name in self.PAGE_MAPPINGS.keys():
            local_path = directory / page_name
            existence[page_name] = local_path.exists()
        
        return existence
    
    def fix_navigation(self, html_path: Path, dry_run: bool = True) -> int:
        """Fix navigation links in a single file"""
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check which pages exist locally
        existence = self.check_local_pages_exist(html_path)
        
        new_content = content
        changes_made = 0
        
        for page_name, guide_path in self.PAGE_MAPPINGS.items():
            if not existence[page_name]:
                # Page doesn't exist locally, update to guide path
                old_href = f'href="{page_name}"'
                new_href = f'href="{guide_path}"'
                
                if old_href in new_content:
                    new_content = new_content.replace(old_href, new_href)
                    changes_made += 1
                    print(f"  {page_name} → {guide_path}")
        
        if changes_made > 0 and not dry_run:
            # Backup original
            backup_path = html_path.with_suffix('.html.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Write fixed content
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.fixes_applied += changes_made
        
        return changes_made
    
    def process_districts(self, dry_run: bool = True):
        """Process all district HTML files"""
        
        districts_dir = self.base_dir / 'districts'
        
        if not districts_dir.exists():
            print(f"Districts directory not found: {districts_dir}")
            return
        
        print(f"{'DRY RUN - ' if dry_run else ''}Scanning district pages...\n")
        
        html_files = list(districts_dir.rglob('*.html'))
        print(f"Found {len(html_files)} HTML files in districts/\n")
        
        files_updated = 0
        
        for html_file in html_files:
            # Check if file has the navigation block
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'cse-meeting-guide.html' in content:
                relative_path = html_file.relative_to(self.base_dir)
                changes = self.fix_navigation(html_file, dry_run)
                
                if changes > 0:
                    print(f"\n{'→' if dry_run else '✓'} {relative_path}")
                    files_updated += 1
        
        print(f"\n{'Would update' if dry_run else 'Updated'} {files_updated} files")
        if dry_run:
            print("Run with --apply to make actual changes")
        else:
            print(f"Total link fixes: {self.fixes_applied}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix district navigation menus'
    )
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory (default: current directory)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply fixes (default: dry run)'
    )
    
    args = parser.parse_args()
    
    fixer = NavigationFixer(args.base_dir)
    fixer.process_districts(dry_run=not args.apply)


if __name__ == '__main__':
    main()