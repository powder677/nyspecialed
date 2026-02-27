import os
import re
from bs4 import BeautifulSoup

# === CONFIGURATION ===
BASE_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"
THIN_THRESHOLD = 800  # word count minimum
REQUIRED_LINKS = [
    "special-ed-updates.html",
    "partners.html"
]

# ======================

def count_words_from_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

        # Remove script/style
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        words = re.findall(r'\b\w+\b', text)
        return len(words), text


def check_missing_links(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    missing = []
    for link in REQUIRED_LINKS:
        if link not in content:
            missing.append(link)
    return missing


def audit_site():
    thin_pages = []
    missing_links_pages = []

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)

                word_count, _ = count_words_from_html(filepath)

                if word_count < THIN_THRESHOLD:
                    thin_pages.append((filepath, word_count))

                missing_links = check_missing_links(filepath)
                if missing_links:
                    missing_links_pages.append((filepath, missing_links))

    print("\n=== THIN CONTENT REPORT ===")
    if thin_pages:
        for page, words in thin_pages:
            print(f"⚠️ THIN CONTENT ({words} words): {page}")
    else:
        print("No thin pages found.")

    print("\n=== MISSING LINKS REPORT ===")
    if missing_links_pages:
        for page, links in missing_links_pages:
            print(f"🔗 MISSING LINKS in {page}: {', '.join(links)}")
    else:
        print("No missing links found.")


if __name__ == "__main__":
    audit_site()