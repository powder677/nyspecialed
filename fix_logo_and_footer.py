import os
import re

def fix_css_header_height(css_path):
    """Updates the header height and dropdown positions in the CSS."""
    if not os.path.exists(css_path):
        print(f"⚠️ CSS file not found: {css_path}")
        return

    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()

    # 1. Update .site-header height
    css_content = re.sub(
        r'(\.site-header\s*\{[^}]*?height:\s*)70px(;\n?)',
        r'\g<1>100px\g<2>',
        css_content
    )

    # 2. Update mega-menu and dropdown-menu top position
    css_content = re.sub(
        r'(\.mega-menu,\s*\.dropdown-menu\s*\{[^}]*?top:\s*)70px(;\n?)',
        r'\g<1>100px\g<2>',
        css_content
    )

    # 3. Increase .nav-logo img height in CSS to 80px (from 50px)
    css_content = re.sub(
        r'(\.nav-logo img\s*\{[^}]*?height:\s*)50px(;\n?)',
        r'\g<1>80px\g<2>',
        css_content
    )

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    print(f"✅ Updated CSS header constraints in {css_path}")

def fix_html_files(root_dir):
    """Scans all HTML files to fix the footer domain and clean inline logo styles."""
    html_files_modified = 0

    # Regex to find the logo img tag and remove its conflicting inline style
    # We want to remove: style="display:block; height:80px; width:auto; border-radius:8px;"
    logo_style_pattern = re.compile(r'(<img src="/images/logo(?:-nav)?\.png"[^>]*?)\s*style="[^"]*height:\s*80px[^"]*"([^>]*>)')
    
    # Regex for footer typo
    bad_domain_pattern1 = re.compile(r'nyspecialed\.com', re.IGNORECASE)
    bad_domain_pattern2 = re.compile(r'ny specialed\.com', re.IGNORECASE)

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".html"):
                filepath = os.path.join(dirpath, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # Fix 1: Strip the inline style from the logo so the CSS can control it perfectly
                content = logo_style_pattern.sub(r'\1\2', content)

                # Fix 2: Replace incorrect footer/domain references globally
                content = bad_domain_pattern1.sub('newyorkspecialed.net', content)
                content = bad_domain_pattern2.sub('newyorkspecialed.net', content)

                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    html_files_modified += 1

    print(f"✅ Successfully cleaned inline logo styles and fixed footer domains in {html_files_modified} HTML files.")

if __name__ == "__main__":
    current_directory = os.getcwd()
    css_file = os.path.join(current_directory, 'styles', 'styles-nav-footer.css')
    
    print("🚀 Starting UI Cleanup...")
    fix_css_header_height(css_file)
    fix_html_files(current_directory)
    print("🏁 Cleanup complete. The logo will now sit perfectly inside a 100px header.")