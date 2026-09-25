import os
import re
from pathlib import Path

# Configuration: Update to your project's root directory if needed
HTML_DIR = "./"

# Regex pattern to match the entire .offers-container block from opening <div class="offers-container"...> 
# to its closing </div> tags before the main container closes.
OFFERS_PATTERN = re.compile(
    r'<div\s+class="offers-container"[^>]*id="premium-offers">.*?</style>\s*<div\s+class="offers-container"[^>]*>.*?(?=</div>\s*</div>\s*</main>)</div>\s*</div>',
    re.DOTALL | re.IGNORECASE
)

# Alternative robust pattern if styling blocks vary slightly:
# Matches from <div class="offers-container" id="premium-offers"> all the way to its last closing tags.
FALLBACK_PATTERN = re.compile(
    r'<div\s+class="offers-container"\s+id="premium-offers">.*?(?=<div class="footer-container">|</main></body>)',
    re.DOTALL | re.IGNORECASE
)

def clean_html_files():
    html_path = Path(HTML_DIR)
    modified_count = 0
    
    for file_path in html_path.glob("**/*.html"):
        # Skip hidden directories
        if "." in file_path.parts[0]:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Check if the offers section exists in the file
            if 'id="premium-offers"' in content or 'offers-container' in content:
                # Apply regex removal
                new_content, count = FALLBACK_PATTERN.subn('', content)
                
                if count > 0:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    modified_count += 1
                    print(f"Removed offers section from: {file_path}")
                else:
                    print(f"Could not cleanly match pattern in: {file_path}")
                    
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"\nCleanup complete! Removed offers block from {modified_count} files.")

if __name__ == "__main__":
    clean_html_files()