# File: fix_og_images.py
import os
import re

html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
default_og_image = "https://www.newyorkspecialed.net/assets/images/social-default.jpg"

og_image_tag = f'\n    <meta property="og:image" content="{default_og_image}" />'
twitter_image_tag = f'\n    <meta name="twitter:image" content="{default_og_image}" />'

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
            
            modified = False
            
            # Inject og:image if missing
            if 'og:image' not in html and '</head>' in html:
                html = html.replace('</head>', f'{og_image_tag}</head>')
                modified = True
                
            # Inject twitter:image if missing
            if 'twitter:image' not in html and '</head>' in html:
                html = html.replace('</head>', f'{twitter_image_tag}</head>')
                modified = True
                
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"[INJECTED OG:IMAGE] {os.path.relpath(filepath, html_dir)}")