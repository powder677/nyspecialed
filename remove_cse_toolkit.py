import os
from bs4 import BeautifulSoup

def remove_cse_toolkit(root_dir="."):
    modified_count = 0
    
    # Recursively walk through all directories and subdirectories
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(subdir, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                soup = BeautifulSoup(content, 'html.parser')
                changed = False
                
                # Method 1: Target the standard 'sidebar-right' container holding the toolkit
                sidebar_right = soup.find('div', class_='sidebar-right')
                if sidebar_right and 'CSE Meeting' in sidebar_right.get_text():
                    sidebar_right.decompose()
                    changed = True
                
                # Method 2: Fallback check for any standalone 'premium-card' matching the toolkit
                if not changed:
                    for card in soup.find_all('div', class_='premium-card'):
                        if 'CSE Meeting' in card.get_text():
                            parent_col = card.find_parent('div', class_='sidebar-right')
                            if parent_col:
                                parent_col.decompose()
                            else:
                                card.decompose()
                            changed = True
                            break

                # Save the file only if changes were made
                if changed:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    modified_count += 1
                    print(f"Removed toolkit from: {filepath}")

    print(f"\nDone! Successfully updated {modified_count} HTML files.")

if __name__ == '__main__':
    # Run this from the root folder of your 550-page project
    remove_cse_toolkit(".")