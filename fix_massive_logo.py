import os
import re

def fix_css_and_html(root_dir):
    css_path = os.path.join(root_dir, 'styles', 'styles-nav-footer.css')
    
    # 1. FIX THE CSS CONSTRAINTS
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        
        # Expand header height to 130px to fit the 120px logo
        css = re.sub(r'(\.site-header\s*\{[^}]*?height:\s*)\d+px', r'\g<1>130px', css)
        
        # Push dropdown top positions down to 130px so they don't overlap the logo
        css = re.sub(r'(\.mega-menu,\s*\.dropdown-menu\s*\{[^}]*?top:\s*)\d+px', r'\g<1>130px', css)
        
        # Force nav-logo img height constraint
        css = re.sub(r'(\.nav-logo img\s*\{[^}]*?height:\s*)\d+px', r'\g<1>120px', css)
        
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css)
        print("✅ CSS constraints updated: Header expanded to 130px.")
    else:
        print(f"⚠️ Could not find CSS at {css_path}")
        
    # 2. FIX ALL HTML FILES (Logo sizing and Footer domain scrub)
    html_files_modified = 0
    logo_pattern = re.compile(r'(<img\s+src="/images/logo\.png"[^>]*?>)')
    
    # Catch any possible variation of the wrong domain
    bad_domains = [
        re.compile(r'nyspecialed\.com', re.IGNORECASE),
        re.compile(r'ny\s*specialed\.com', re.IGNORECASE),
        re.compile(r'new\s*york\s*special\s*ed\.com', re.IGNORECASE)
    ]
    
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".html"):
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                orig_content = content
                
                # REBUILD LOGO TAG
                def replace_logo(match):
                    img_tag = match.group(1)
                    # Strip out all old width/height/style attributes
                    img_tag = re.sub(r'\s+width="\d+"', '', img_tag)
                    img_tag = re.sub(r'\s+height="\d+"', '', img_tag)
                    img_tag = re.sub(r'\s+style="[^"]*"', '', img_tag)
                    # Clean the end of the tag
                    img_tag = re.sub(r'\s*/?>$', '', img_tag)
                    # Inject exactly what you requested
                    return img_tag + ' width="120" height="120" style="display:block; height:120px; width:auto; border-radius:8px;" />'
                    
                content = logo_pattern.sub(replace_logo, content)
                
                # OBLITERATE FOOTER TYPOS
                for bd in bad_domains:
                    content = bd.sub('newyorkspecialed.net', content)
                    
                # Save if changes were made
                if content != orig_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    html_files_modified += 1
                    
    print(f"✅ Modified {html_files_modified} HTML files.")
    print("✅ Injected width='120' height='120' and inline styles into the logo.")
    print("✅ Scrubbed all wrong .com domain references into newyorkspecialed.net.")

if __name__ == "__main__":
    print("🚀 Starting Aggressive Fix...")
    fix_css_and_html(os.getcwd())
    print("🏁 Done.")