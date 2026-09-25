import os
import re
from pathlib import Path

# Configuration
HTML_DIR = "./"  # Update to your target directory containing the HTML files
JS_OUTPUT_DIR = "./scripts"
JS_FILENAME = "newsletter-popup.js"

# Regex pattern to find the inline email capture script block
# Matches from <script data-api=... id="ec-script"> up to </script>
SCRIPT_PATTERN = re.compile(
    r'<script\s+[^>]*id="ec-script"[^>]*>.*?</script>', 
    re.DOTALL | re.IGNORECASE
)

def refactor_html_files():
    html_path = Path(HTML_DIR)
    js_dir = Path(JS_OUTPUT_DIR)
    js_dir.mkdir(parents=True, exist_ok=True)
    
    js_file_path = js_dir / JS_FILENAME
    extracted_js_content = None

    modified_count = 0
    
    # Iterate through all HTML files recursively
    for file_path in html_path.glob("**/*.html"):
        # Skip files inside the output script directory or hidden folders
        if "scripts" in file_path.parts or "." in file_path.parts[0]:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            match = SCRIPT_PATTERN.search(content)
            if match:
                script_block = match.group(0)
                
                # If we haven't extracted the JS code yet, grab it from the first match
                if not extracted_js_content:
                    # Strip the opening and closing <script> tags to get pure JS
                    inner_js = re.sub(r'<\/?script[^>]*>', '', script_block, flags=re.IGNORECASE).strip()
                    extracted_js_content = inner_js
                    
                    # Save the extracted script to the external file if it doesn't exist
                    if not js_file_path.exists():
                        with open(js_file_path, "w", encoding="utf-8") as jf:
                            jf.write(extracted_js_content)
                        print(f"Created external script asset: {js_file_path}")

                # Replace the bulky inline script with a lightweight deferred reference
                replacement = f'<script src="/scripts/{JS_FILENAME}" defer></script>'
                new_content = content.replace(script_block, replacement)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                    
                modified_count += 1
                print(f"Updated: {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"\nRefactoring complete! Updated {modified_count} HTML files.")

if __name__ == "__main__":
    refactor_html_files()