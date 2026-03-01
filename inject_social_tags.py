# File: inject_social_tags.py
import os
from bs4 import BeautifulSoup

# Target directory provided
html_dir = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
base_url = "https://www.newyorkspecialed.net"

for root, dirs, files in os.walk(html_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            
            # Calculate canonical URL based on file path for og:url
            rel_path = os.path.relpath(filepath, html_dir)
            url_path = rel_path.replace('\\', '/').replace('index.html', '')
            page_url = f"{base_url}/{url_path}"

            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            head = soup.find('head')
            if not head:
                continue # Skip files missing a head block

            modified = False

            # Extract existing title and description
            title_tag = soup.find('title')
            title_text = title_tag.string.strip() if title_tag and title_tag.string else "NY Special Education"
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            desc_text = meta_desc['content'].strip() if meta_desc and meta_desc.has_attr('content') else ""

            # Define required social tags
            social_tags = [
                {'property': 'og:type', 'content': 'website'},
                {'property': 'og:title', 'content': title_text},
                {'property': 'og:description', 'content': desc_text},
                {'property': 'og:url', 'content': page_url},
                {'name': 'twitter:card', 'content': 'summary_large_image'},
                {'name': 'twitter:title', 'content': title_text},
                {'name': 'twitter:description', 'content': desc_text}
            ]

            # Inject missing tags
            for tag_data in social_tags:
                attr_name = 'property' if 'property' in tag_data else 'name'
                existing_tag = soup.find('meta', attrs={attr_name: tag_data[attr_name]})
                
                if not existing_tag:
                    new_meta = soup.new_tag('meta', attrs=tag_data)
                    head.append(new_meta)
                    modified = True
                elif existing_tag['content'] != tag_data['content']:
                    # Update existing tag if it's out of sync with the new title/desc
                    existing_tag['content'] = tag_data['content']
                    modified = True

            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"[INJECTED SOCIAL TAGS] {rel_path}")