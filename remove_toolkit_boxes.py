import os
from bs4 import BeautifulSoup

def remove_toolkit_boxes(directory="."):
    # Walk through all directories and files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                with open(filepath, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                soup = BeautifulSoup(html_content, "html.parser")
                modified = False
                
                # Target the box by checking class or contents
                # It typically has class "cta-box" or contains the header "Need More Help?"
                for box in soup.find_all(lambda tag: tag.name in ["div", "section"] and (
                    (tag.get("class") and "cta-box" in tag.get("class")) or
                    (tag.find(lambda t: t.name in ["h3", "h4"] and "Need More Help?" in t.get_text()))
                )):
                    # Optional extra validation to ensure it's the toolkit box
                    text_content = box.get_text()
                    if "Need More Help?" in text_content and "toolkit" in text_content.lower():
                        box.decompose()
                        modified = True

                # Save the file back if changes were made
                if modified:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    print(f"Removed toolkit box from: {filepath}")

if __name__ == "__main__":
    print("Scanning HTML files for the toolkit box...")
    remove_toolkit_boxes(".")
    print("Done!")