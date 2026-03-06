import os
from bs4 import BeautifulSoup

# The target directory for your parent guides
TARGET_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed\guides"

# The 2 Cards (Offers Container) to go at the bottom of the 70% content side
OFFERS_HTML = """
<style>
    /* STACKED OFFERS FOR NEW YORK */
    .offers-container { display: flex; flex-direction: column; gap: 24px; margin-top: 50px; border-top: 2px solid #e2e8f0; padding-top: 40px; }
    .offers-title { font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; color: #002868; text-align: center; margin: 0 0 5px 0; border: none; padding: 0;}
    .offers-subtitle { text-align: center; color: #475569; font-family: 'DM Sans', sans-serif; margin-bottom: 25px; font-size: 1.1rem;}
    
    .sales-card { background: linear-gradient(135deg, #002868 0%, #1e3a8a 100%); padding: 36px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15); position: relative; overflow: hidden; }
    .sales-card .badge { background: #d4af37; color: #002868; padding: 6px 16px; border-radius: 50px; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; display: inline-block; margin-bottom: 15px;}
    .sales-card h3 { margin: 0 0 12px; color: #ffffff; font-size: 1.8rem; font-family: 'Cormorant Garamond', serif; }
    .sales-card p { color: #e2e8f0; margin: 0 auto 24px; font-size: 1.05rem; line-height: 1.6; max-width: 90%; font-family: 'DM Sans', sans-serif;}
    .sales-card a.buy-btn { background: #d4af37; color: #002868; padding: 16px 32px; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 1.1rem; display: inline-block; transition: 0.2s; font-family: 'DM Sans', sans-serif;}
    .sales-card a.buy-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(212,175,55,0.4); }

    .sales-card.coming-soon { background: linear-gradient(135deg, #475569 0%, #334155 100%); }
    .sales-card.coming-soon .badge { background: #94a3b8; color: #1e293b; }
    .sales-card.coming-soon p { color: #cbd5e1; }
    .sales-card.coming-soon a.buy-btn { background: #64748b; color: #f8fafc; cursor: not-allowed; }
    
    .coming-soon-overlay {
        position: absolute;
        top: 28px;
        right: -45px;
        background: #d4af37;
        color: #002868;
        padding: 8px 50px;
        font-weight: 800;
        font-size: 0.85rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        transform: rotate(45deg);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        z-index: 2;
        font-family: 'DM Sans', sans-serif;
    }
</style>
<div class="offers-container" id="premium-offers">
    <h2 class="offers-title">Take the Next Step</h2>
    <p class="offers-subtitle">Protect your child's right to a Free Appropriate Public Education.</p>
    
    <div class="sales-card">
        <span class="badge">Essential</span>
        <h3>The CSE Meeting Prep Kit</h3>
        <p>Master the NY Special Education evaluation and IEP process. Includes independent evaluation (IEE) request templates, 60-day timeline trackers, and exact scripts to use at your meeting.</p>
        <a class="buy-btn" href="/contact/">Get the Prep Kit — $47</a>
    </div>
    
    <div class="sales-card coming-soon">
        <div class="coming-soon-overlay">Coming Soon</div>
        <span class="badge">Advanced</span>
        <h3>The CSE Kit + Autism Pack</h3>
        <p>Everything in the standard Prep Kit, plus specialized autism IEP goals, sensory diet accommodations, and FBA/BIP behavioral strategies tailored specifically for New York schools.</p>
        <a class="buy-btn" href="#" onclick="return false;">Available Next Month</a>
    </div>
</div>
"""

# The Sidebar Bot for the 30% side
SIDEBAR_HTML = """
<div class="premium-sidebar-right" style="flex: 1 1 30%; min-width: 300px; position: sticky; top: 20px;">
    <div id="iep-bot-sidebar" style="background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.08); height: 750px; display: flex; flex-direction: column;">
       <div style="background: #2d5248; padding: 20px; text-align: center; color: white;">
          <h3 style="margin: 0 0 5px 0; font-family: 'Lora', serif; font-size: 22px;">IEP Letter Writer</h3>
          <p style="margin: 0; font-size: 14px; color: #e2e8f0;">Generate your custom request in minutes.</p>
       </div>
       <iframe loading="lazy" src="https://iep-letter-writer-831148457361.us-central1.run.app" width="100%" height="100%" style="border:none; flex-grow: 1;"></iframe>
    </div>
</div>
"""

def format_page(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip the root guides/index.html (the hub page shouldn't be a reading article)
    if os.path.dirname(filepath).rstrip('\\/') == TARGET_DIR.rstrip('\\/'):
        print(f"Skipped (Root Hub): {os.path.basename(filepath)}")
        return

    # Prevent formatting pages that are already properly formatted
    if 'iep-bot-sidebar' in content and 'premium-split-container' in content:
        print(f"Skipped (Already Formatted): {os.path.relpath(filepath, TARGET_DIR)}")
        return

    soup = BeautifulSoup(content, 'html.parser')
    
    # Aggressively look for the main content area
    main_tag = soup.find('main')
    if not main_tag:
        # Fallback if there is no <main> tag
        main_tag = soup.find('div', class_='container')
        
    if not main_tag:
        print(f"Warning: Could not find <main> or <div class='container'> in {os.path.relpath(filepath, TARGET_DIR)}")
        return

    # STEP 1: Rip out old sidebars or botched attempts so we have a clean slate
    for old_sidebar in main_tag.find_all('div', class_='premium-sidebar-right'):
        old_sidebar.decompose()
    for old_offers in main_tag.find_all('div', class_='offers-container'):
        old_offers.decompose()
    for old_split in main_tag.find_all('div', class_='premium-split-container'):
        # Extract the content text back out to safety before deleting the old split
        body = old_split.find('div', class_='content-body')
        if body:
            old_split.insert_before(body)
            body.unwrap()
        old_split.decompose()

    # STEP 2: Identify what goes in the 70% content area vs. what stays at the top
    elements_to_move = []
    
    # Classes we want to leave outside the split container (e.g. breadcrumbs, titles)
    leave_outside = ['aeo-authority-block', 'breadcrumb', 'district-subnav', 'page-header', 'hero-section']

    for child in main_tag.children:
        # Ignore empty newlines
        if child.name is None and not child.text.strip():
            continue
            
        # Check if the element is a top-level nav/breadcrumb to leave alone
        if child.name and child.get('class'):
            if any(cls in leave_outside for cls in child.get('class')):
                continue
                
        elements_to_move.append(child)

    if not elements_to_move:
        print(f"Warning: Main area is empty in {os.path.relpath(filepath, TARGET_DIR)}")
        return

    # STEP 3: Build the new 70/30 split structure
    split_container = soup.new_tag('div', attrs={
        'class': 'premium-split-container', 
        'style': 'display: flex; flex-wrap: wrap; gap: 40px; align-items: flex-start; width: 100%; margin-top: 30px;'
    })
    
    content_body = soup.new_tag('div', attrs={
        'class': 'content-body', 
        'style': 'flex: 1 1 60%; min-width: 300px; max-width: 100%; padding: 0; margin-top: 0;'
    })

    # Move the page content into the 70% left side
    for elem in elements_to_move:
        extracted = elem.extract()
        content_body.append(extracted)

    # Append the 2 Offers Cards to the bottom of the 70% left side
    offers_soup = BeautifulSoup(OFFERS_HTML, 'html.parser')
    content_body.append(offers_soup)
    split_container.append(content_body)

    # Append the AI Bot to the 30% right side
    sidebar_soup = BeautifulSoup(SIDEBAR_HTML, 'html.parser')
    split_container.append(sidebar_soup)

    # Put the split layout back into the main document
    main_tag.append(split_container)

    # Save changes
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"Success - Formatted 70/30: {os.path.relpath(filepath, TARGET_DIR)}")


def main():
    if not os.path.exists(TARGET_DIR):
        print(f"Error: Directory not found -> {TARGET_DIR}")
        return

    print(f"Scanning directory: {TARGET_DIR}")
    files_processed = 0

    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            if file.lower().endswith('.html'):
                filepath = os.path.join(root, file)
                format_page(filepath)
                files_processed += 1

    print(f"\nDone! Scanned {files_processed} total HTML files in the guides folder.")

if __name__ == "__main__":
    main()