# File: fix_onpage_seo.py
import os
from bs4 import BeautifulSoup

# Updated to your local working directory
html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
brand_name = " | New York Special Ed" # Used for title truncation

def smart_truncate(content, length=55, suffix=''):
    if len(content) <= length:
        return content
    else:
        # Prevent crash if there are no spaces in the string
        if ' ' in content[:length]:
            return content[:length].rsplit(' ', 1)[0] + suffix
        return content[:length] + suffix

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            modified = False

            # 1. FIX OVERSIZED TITLES
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                title_text = title_tag.string.strip()
                if len(title_text) > 60:
                    # Truncate and append brand name safely
                    new_title = smart_truncate(title_text, length=60 - len(brand_name)) + brand_name
                    title_tag.string = new_title
                    modified = True

            # 2. FIX MISSING OR SHORT META DESCRIPTIONS
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            desc_text = meta_desc['content'].strip() if meta_desc and meta_desc.has_attr('content') else ""
            
            if not meta_desc or len(desc_text) < 70:
                # Find the first paragraph to use as a fallback description
                first_p = soup.find('p')
                if first_p and first_p.text:
                    fallback_text = smart_truncate(first_p.text.strip(), length=155, suffix='...')
                    if not meta_desc:
                        # Inject new meta tag
                        head = soup.find('head')
                        if head:
                            new_meta = soup.new_tag('meta', attrs={'name': 'description', 'content': fallback_text})
                            head.append(new_meta)
                            modified = True
                    else:
                        # Update existing short meta tag
                        meta_desc['content'] = fallback_text
                        modified = True

            # 3. FIX MISSING H1 TAGS
            h1_tag = soup.find('h1')
            if not h1_tag or not h1_tag.text.strip():
                # No H1 found. Create one from the title tag (minus the brand name)
                if title_tag and title_tag.string:
                    clean_h1_text = title_tag.string.split('|')[0].strip()
                    new_h1 = soup.new_tag('h1')
                    new_h1.string = clean_h1_text
                    
                    # Try to inject it into <main> or <body>
                    target_container = soup.find('main') or soup.find('body')
                    if target_container:
                        target_container.insert(0, new_h1)
                        modified = True
            
            # Save if changes were made
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Write the modified HTML back to the file
                    f.write(str(soup))
                print(f"[FIXED] {filepath}")