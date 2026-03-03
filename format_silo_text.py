import os
import re
from bs4 import BeautifulSoup

def parse_dense_content(raw_html):
    # 1. Fix broken placeholder links from AI generation
    raw_html = raw_html.replace('(LINK TO EVALUATION PAGE)', '(evaluation-process.html)')
    raw_html = raw_html.replace('(LINK TO CSE MEETING PAGE)', '(cse-meeting-guide.html)')
    raw_html = raw_html.replace('(LINK TO IEP PAGE)', '(/guides/cse-meeting-guide/)')
    raw_html = raw_html.replace('(LINK TO DISPUTE RESOLUTION PAGE)', '(/guides/dispute-resolution-ny/)')
    raw_html = raw_html.replace('(LINK TO PARENT RIGHTS PAGE)', '(/guides/)')
    raw_html = raw_html.replace('(LINK TO RESOURCES PAGE)', '(/resources/)')

    # 2. Convert Markdown Links: [Text](URL) -> <a href="URL">Text</a>
    raw_html = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)', 
        r'<a href="\2" style="color: #0056b3; font-weight: 600; text-decoration: none; border-bottom: 1px solid #0056b3;">\1</a>', 
        raw_html
    )

    # 3. Convert Markdown Bold: **text** -> <strong>text</strong>
    raw_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', raw_html)
    
    # 4. Split the giant text block into individual chunks wherever there is a double line break
    blocks = re.split(r'\n\s*\n', raw_html)
    
    parsed_blocks = []
    in_list = False
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # --- Handle Existing HTML Tags (Like <h2>) ---
        if block.startswith('<h') or block.startswith('<div') or block.startswith('<section') or block.startswith('<p'):
            if in_list:
                parsed_blocks.append('</ul>')
                in_list = False
            
            # Make the H2 subheadings look premium and give them breathing room
            if block.startswith('<h2>'):
                block = block.replace('<h2>', '<h2 style="color: #002868; font-size: 2rem; margin-top: 50px; margin-bottom: 20px; border-bottom: 2px solid #d4af37; padding-bottom: 10px; font-family: \'Cormorant Garamond\', serif;">')
            
            parsed_blocks.append(block)
            continue
            
        # --- Handle Bulleted Lists (* Item) ---
        if block.startswith('* ') or block.startswith('- '):
            if not in_list:
                # Start a new UL with nice spacing
                parsed_blocks.append('<ul style="margin-top: 15px; margin-bottom: 30px; padding-left: 25px; line-height: 1.8; color: #334155; font-size: 1.1rem;">')
                in_list = True
            
            # Split the block by single newlines to get each list item
            list_items = block.split('\n')
            for item in list_items:
                item = item.strip()
                if item.startswith('* ') or item.startswith('- '):
                    parsed_blocks.append(f'<li style="margin-bottom: 12px; padding-left: 8px;">{item[2:].strip()}</li>')
                elif item:
                    parsed_blocks.append(f'{item}') 
            continue
            
        # Close list if we hit normal text
        if in_list:
            parsed_blocks.append('</ul>')
            in_list = False
            
        # --- Handle Normal Paragraphs ---
        # Wrap the raw text in a beautifully spaced paragraph tag
        parsed_blocks.append(f'<p style="margin-bottom: 28px; line-height: 1.85; color: #334155; font-size: 1.125rem;">{block}</p>')
            
    if in_list:
        parsed_blocks.append('</ul>')
        
    return '\n'.join(parsed_blocks)

def main():
    print("Scanning for index.html files to format text...")
    
    files_to_process = []
    for root, dirs, files in os.walk('.'):
        parts = root.split(os.sep)
        if 'districts' in parts and parts[-1] != 'districts':
            if 'index.html' in files:
                files_to_process.append(os.path.join(root, 'index.html'))
                
    if not files_to_process:
        print("ERROR: Could not find any district index.html files.")
        return

    count = 0
    for file_path in files_to_process:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the content column we created in the last step
        target_container = soup.find('div', class_='premium-content-left')
        
        # Fallback just in case the last script didn't run on this file
        if not target_container:
            target_container = soup.find('section', class_='local-aeo-section')
            
        if not target_container:
            print(f"[SKIPPED] {file_path} - Could not find content container.")
            continue
            
        # 1. Extract the raw text/HTML
        inner_html = target_container.decode_contents()
        
        # 2. Skip if it looks like we already formatted it (it will have lots of our custom <p> tags)
        if '<p style="margin-bottom: 28px;' in inner_html:
            print(f"[SKIPPED] {file_path} - Already formatted.")
            continue
            
        # 3. Process the text through our Markdown parser
        parsed_html = parse_dense_content(inner_html)
        
        # 4. Clear the old unformatted text and inject the newly formatted HTML
        target_container.clear()
        new_soup = BeautifulSoup(parsed_html, 'html.parser')
        target_container.append(new_soup)
            
        # 5. Save the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        count += 1
        print(f"[SUCCESS] Parsed and Formatted text in: {file_path}")

    print(f"\n======================================")
    print(f"DONE! Formatted content on {count} pages.")
    print(f"======================================")

if __name__ == '__main__':
    main()