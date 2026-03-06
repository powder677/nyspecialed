import os
from bs4 import BeautifulSoup, Comment

# The target directory you provided
TARGET_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\districts"

TOP_BANNER_HTML = """
<!-- Top Banner Anchor to Bot -->
<div style="background: #2d5248; color: white; padding: 16px 24px; border-radius: 8px; margin-top: 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 12px rgba(0,0,0,0.1); flex-wrap: wrap; gap: 16px;">
   <div style="display: flex; align-items: center; gap: 12px;">
      <span style="background: #c9973a; color: #2d5248; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; letter-spacing: 0.1em;">NEW</span>
      <span style="font-family:'Lora',serif; font-size:18px; font-weight:700;">Get Your IEP Letter Written by our AI Bot</span>
   </div>
   <a href="#iep-bot-sidebar" style="background: #c9973a; color: #2d5248; font-weight: 800; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; white-space: nowrap; transition: background 0.2s;">Start Now — $15 →</a>
</div>
"""

NEW_SIDEBAR_CONTENT = """
<div id="iep-bot-sidebar" style="background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.08); height: 750px; display: flex; flex-direction: column;">
   <div style="background: #2d5248; padding: 20px; text-align: center; color: white;">
      <h3 style="margin: 0 0 5px 0; font-family: 'Lora', serif; font-size: 22px;">IEP Letter Writer</h3>
      <p style="margin: 0; font-size: 14px; color: #e2e8f0;">Generate your custom request in minutes.</p>
   </div>
   <iframe loading="lazy" src="https://iep-letter-writer-831148457361.us-central1.run.app" width="100%" height="100%" style="border:none; flex-grow: 1;"></iframe>
</div>
"""

def process_file(filepath):
    # Read the original HTML file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip files that already have the bot inserted to prevent duplicating the banner
    if 'id="iep-bot-sidebar"' in content and 'Top Banner Anchor to Bot' in content:
        print(f"Skipped (Already Updated): {os.path.basename(filepath)}")
        return

    soup = BeautifulSoup(content, 'html.parser')
    modified = False

    # 1. Update the Right Sidebar
    sidebar = soup.find('div', class_='premium-sidebar-right')
    if sidebar:
        # Clear out whatever is currently in the sidebar (lawyer form, toolkit, etc.)
        sidebar.clear()
        
        # Parse and insert the new bot iframe
        sidebar_soup = BeautifulSoup(NEW_SIDEBAR_CONTENT, 'html.parser')
        sidebar.append(sidebar_soup)
        modified = True
    else:
        print(f"Warning: Could not find 'premium-sidebar-right' in {os.path.basename(filepath)}")

    # 2. Insert the Top Banner Anchor
    # Look for the end of the sub-navigation comment
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    subnav_comment = next((c for c in comments if '__district-subnav-end__' in c), None)

    banner_soup = BeautifulSoup(TOP_BANNER_HTML, 'html.parser')

    if subnav_comment:
        subnav_comment.insert_after(banner_soup)
        modified = True
    else:
        # Fallback: If comment is missing, insert it right before the split layout container
        split_container = soup.find('div', class_='premium-split-container')
        if split_container:
            split_container.insert_before(banner_soup)
            modified = True
        else:
             print(f"Warning: Could not find insertion point for the top banner in {os.path.basename(filepath)}")

    # Save the file if changes were made
    if modified:
        # str(soup) writes back the HTML structure
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"Success - Updated: {os.path.basename(filepath)}")


def main():
    print(f"Scanning directory: {TARGET_DIR}")
    files_processed = 0

    # Walk through all folders and subfolders in the target directory
    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            # Only target HTML files and explicitly exclude 'partners' pages
            if file.endswith('.html') and 'partners' not in file.lower():
                filepath = os.path.join(root, file)
                process_file(filepath)
                files_processed += 1

    print(f"\nDone! Scanned {files_processed} eligible files.")

if __name__ == "__main__":
    main()