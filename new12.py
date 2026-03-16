import os
import re

# --- Configuration ---
WEBSITE_ROOT_DIR = '.'
DISTRICTS_FOLDER = os.path.join(WEBSITE_ROOT_DIR, 'districts')

def format_district_name(slug):
    """Converts a slug like 'nyc-district-27-rockaway' to 'NYC District 27 Rockaway'."""
    if not slug:
        return "District"
    
    # Replace dashes with spaces
    name = slug.replace('-', ' ')
    
    # Capitalize words, but ensure 'NYC' is fully capitalized
    words = name.split()
    formatted_words = [word.upper() if word.lower() == 'nyc' else word.capitalize() for word in words]
    
    # Handle 'sd' or 'ufsd' as uppercase
    formatted_words = [word.upper() if word.lower() in ['sd', 'ufsd'] else word for word in formatted_words]
    
    return " ".join(formatted_words)

def get_corrected_html_block(district_slug):
    """Generates the localized navigation block."""
    district_name = format_district_name(district_slug)
    
    return f"""<strong>
      {district_name} Resources:
     </strong>
     <a href="index.html">
      District Home
     </a>
     <a href="cse-meeting-guide.html">
      CSE Guide
     </a>
     <a href="evaluation-process.html">
      Evaluations
     </a>
     <a href="discipline-rights.html">
      Discipline Rights
     </a>
     <a href="leadership-directory.html">
      Contacts
     </a>
     <a href="special-ed-updates.html">
      Updates
     </a>
     <a href="partners.html">
      Providers &amp; Support
     </a>
     <a class="active" href="parent-advocacy-guide.html">
      Advocacy Guide
     </a>
    </nav>
    <div class="trust-anchor">
     <strong>
      Hi, I'm a New York parent of a child with an IEP.
     </strong>
     When I watched the system fail my child, I realized how broken the CSE process is. I built this resource to help parents like you get the services your child deserves. You are not alone.
    </div>"""

def patch_template_blocks(districts_dir):
    """Scans all HTML files and replaces the hardcoded Maspeth block."""
    if not os.path.exists(districts_dir):
        print(f"Error: Could not find districts directory at {districts_dir}")
        return

    # Regex to capture the exact block. 
    # re.DOTALL allows .* to span across multiple lines.
    # We look for the starting <strong> tag down to the closing </div> of the trust anchor.
    block_pattern = re.compile(
        r'<strong>\s*NYC District 24 Maspeth Resources:\s*</strong>.*?<div class="trust-anchor">.*?You are not alone\.\s*</div>',
        re.DOTALL | re.IGNORECASE
    )

    files_modified = 0

    for root, dirs, files in os.walk(districts_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                # Extract the district slug from the directory path
                relative_path = os.path.relpath(root, districts_dir)
                if relative_path == '.':
                    continue # Skip root districts folder
                
                district_slug = relative_path.split(os.sep)[0]

                # Read the file
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    continue

                # Search and replace
                if block_pattern.search(content):
                    new_html = get_corrected_html_block(district_slug)
                    new_content = block_pattern.sub(new_html, content)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"[PATCHED] {filepath} -> Localized to '{format_district_name(district_slug)}'")
                    files_modified += 1

    print(f"\n--- Scan Complete ---")
    print(f"Successfully localized {files_modified} files with correct district names and links.")

if __name__ == "__main__":
    print("Initiating Template Block Replacement...")
    patch_template_blocks(DISTRICTS_FOLDER)