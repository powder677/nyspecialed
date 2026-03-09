import os
import re

def update_iep_links_only():
    """
    Scans all HTML files in the project, updating the IEP Letter Writer card
    to point to the new /tools/ page while keeping the price at $15.
    """
    print("Scanning project for IEP bot links...")
    
    # Regex to change the href attribute from the old sidebar ID to the new tools page
    link_pattern = re.compile(r'(<a[^>]*href=)["\']#iep-bot-sidebar["\']([^>]*>)')
    
    updated_count = 0
    
    # Walk through all directories and files recursively
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # If the old sidebar anchor link is found in the file
                if '#iep-bot-sidebar' in content:
                    
                    # 1. Update the destination URL to point to /tools/
                    new_content = link_pattern.sub(r'\1"/tools/"\2', content)
                    
                    # Save the modified file
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                            
                        print(f"✅ Updated link (kept at $15): {filepath}")
                        updated_count += 1
                        
    print(f"\n🎉 Done! Successfully routed the IEP tool link to /tools/ on {updated_count} pages.")

if __name__ == '__main__':
    update_iep_links_only()