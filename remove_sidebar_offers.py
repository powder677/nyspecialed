import os
from bs4 import BeautifulSoup

def remove_sidebar_offers(directory="."):
    # Walk through all directories and files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                with open(filepath, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                
                modified = False
                
                # 1. Target and remove the "District Intelligence" newsletter sidebar card
                # It typically has h4 with text "District Intelligence" or class "sidebar-newsletter"
                newsletter_card = soup.find(lambda tag: tag.name == "div" and (
                    tag.get("class") and "sidebar-newsletter" in tag.get("class") or
                    (tag.find("h4") and "District Intelligence" in tag.find("h4").get_text())
                ))
                
                if newsletter_card:
                    newsletter_card.decompose()
                    modified = True

                # 2. Target and remove the "Free Tools" promo sidebar card
                # It has h4 with text "Free Tools" and a link containing "View All Free Tools"
                for card in soup.find_all("div", class_="sidebar-card"):
                    h4 = card.find("h4")
                    if h4 and "Free Tools" in h4.get_text():
                        # Make sure it's the promo card, not a TOC
                        if card.find("a", string=lambda t: t and "View All Free Tools" in t):
                            card.decompose()
                            modified = True
                            break

                # Save the file back if changes were made
                if modified:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    print(f"Updated (Offers removed): {filepath}")

if __name__ == "__main__":
    print("Scanning HTML files and removing target sidebar offers...")
    remove_sidebar_offers(".")
    print("Done!")