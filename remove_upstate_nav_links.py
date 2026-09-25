import os
from bs4 import BeautifulSoup

def remove_upstate_nav_links(directory="."):
    # Walk through all directories and files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                with open(filepath, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                soup = BeautifulSoup(html_content, "html.parser")
                modified = False
                
                # Find all navigation links (<a> tags)
                for a_tag in soup.find_all("a"):
                    href = a_tag.get("href", "")
                    text = a_tag.get_text().strip()
                    
                    # Target links that reference "Upstate Districts" or contain "upstate" in the href
                    if "upstate" in href.lower() or "upstate districts" in text.lower():
                        # If the parent is a <li>, remove the whole list item to keep layout clean
                        if a_tag.parent and a_tag.parent.name == "li":
                            a_tag.parent.decompose()
                        else:
                            a_tag.decompose()
                        modified = True

                # Save the file back if changes were made
                if modified:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    print(f"Removed Upstate Districts nav link from: {filepath}")

if __name__ == "__main__":
    print("Scanning HTML files for 'Upstate Districts' navigation links...")
    remove_upstate_nav_links(".")
    print("Done!")