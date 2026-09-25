import os
import re
from pathlib import Path

# Configuration: Update to your project's root directory if needed
HTML_DIR = "./"

# Regex to remove the Stacked Offers style block and container entirely
OFFERS_PATTERN = re.compile(
    r'<style>\s*/\* STACKED OFFERS.*?</style>\s*<div class="offers-container".*?</div>\s*</div>',
    re.DOTALL | re.IGNORECASE
)

# Broader fallback regex if spacing or comments differ slightly
FALLBACK_OFFERS_PATTERN = re.compile(
    r'<div class="offers-container" id="premium-offers">.*?</style>.*?</div>\s*</div>\s*</div>',
    re.DOTALL | re.IGNORECASE
)

def clean_and_fix_html():
    html_path = Path(HTML_DIR)
    modified_count = 0
    
    for file_path in html_path.glob("**/*.html"):
        # Skip hidden directories like .git or node_modules
        if any(part.startswith('.') for part in file_path.parts):
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            original_content = content
            
            # 1. Remove the offers style block and container
            content = OFFERS_PATTERN.sub('', content)
            content = FALLBACK_OFFERS_PATTERN.sub('', content)
            
            # Also catch any leftover standalone .offers-container blocks
            standalone_offers = re.compile(r'<div class="offers-container".*?</div>\s*</div>\s*(?=</main>|<div class="footer-container">)', re.DOTALL | re.IGNORECASE)
            content = standalone_offers.sub('', content)

            # 2. Fix the Footer Container / Missing Opening Footer Tag
            # If the file has a stray `</footer>` but no opening `<footer` tag before `<div class="footer-container">`, add it.
            if '<div class="footer-container">' in content and '</footer>' in content:
                # Check if <footer ...> is already present immediately before footer-container
                if not re.search(r'<footer[^>]*>\s*<div class="footer-container">', content):
                    content = content.replace(
                        '<div class="footer-container">', 
                        '<footer class="site-footer">\n<div class="footer-container">'
                    )

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                modified_count += 1
                print(f"Successfully cleaned and fixed footer in: {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"\nBatch complete! Updated {modified_count} HTML files.")

if __name__ == "__main__":
    clean_and_fix_html()