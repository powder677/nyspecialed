import os
import re

# Configuration
WEBSITE_ROOT_DIR = '.'

def generate_new_block(district_slug):
    """Generates the corrected HTML block, dynamically injecting the district name."""
    # Convert slug 'albany-city-sd' to 'Albany City Sd'
    if district_slug:
        district_name = district_slug.replace('-', ' ').title()
    else:
        district_name = "District"

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

def replace_bad_html_block(root_dir):
    # This regex captures everything from the NYC District 24 <strong> tag 
    # down to the closing </div> of the trust anchor.
    # re.DOTALL allows the .* to span across multiple lines of HTML.
    block_pattern = re.compile(
        r'<strong>\s*NYC District 24 Maspeth Resources:\s*</strong>.*?<div class="trust-anchor">.*?You are not alone\.\s*</div>',
        re.DOTALL | re.IGNORECASE
    )

    files_modified = 0

    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith('.html'):
                filepath = os.path.join(dirpath, file)
                
                # Extract the district slug from the path
                path_parts = filepath.split(os.sep)
                district_slug = None
                if 'districts' in path_parts:
                    idx = path_parts.index('districts')
                    if len(path_parts) > idx + 1:
                        district_slug = path_parts[idx + 1]

                # Read the file
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # If the bad block is found, replace it
                if block_pattern.search(content):
                    new_html = generate_new_block(district_slug)
                    
                    # Swap the old code for the new code
                    new_content = block_pattern.sub(new_html, content)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"[REPLACED] {filepath} -> Injected '{district_slug}'")
                    files_modified += 1

    print(f"\nOperation Complete. Successfully updated {files_modified} HTML files.")

if __name__ == "__main__":
    print("Scanning for the hardcoded NYC District 24 block...")
    replace_bad_html_block(WEBSITE_ROOT_DIR)