import os
import re

def polish_homepage_ui(root_dir):
    index_path = os.path.join(root_dir, 'index.html')
    
    if not os.path.exists(index_path):
        print(f"⚠️ Could not find {index_path}")
        return

    print("🚀 Initiating UI Polish on Homepage...")

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # ==========================================
    # 1. FIX HERO TEXT READABILITY
    # ==========================================
    # Replace the existing .hero-title CSS with a high-contrast white version
    hero_title_css = """
        .hero-title {
            font-size: 3rem;
            margin-bottom: 20px;
            font-weight: 800;
            color: #ffffff; /* Forces text to white against the dark gradient */
            text-shadow: 0 2px 4px rgba(0,0,0,0.4); /* Adds depth and separation */
            letter-spacing: -0.5px;
        }"""
    html = re.sub(r'\.hero-title\s*\{[^}]*\}', hero_title_css.strip(), html)
    print("✅ Fixed: Hero text contrast restored (White with shadow).")

    # ==========================================
    # 2. ENHANCE MAIN HUB BOXES
    # ==========================================
    # Upgrade the 3 main cards to look premium and highly clickable
    hub_card_css = """
        .hub-card {
            background: white;
            padding: 30px 25px; 
            border: 1px solid #e2e8f0; 
            border-top: 4px solid #c8102e; /* Brand red anchor line */
            border-radius: 12px; 
            text-decoration: none; 
            color: inherit; 
            display: block;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .hub-card:hover { 
            transform: translateY(-6px); 
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }"""
    html = re.sub(r'\.hub-card\s*\{[^}]*\}', hub_card_css.strip(), html)
    html = re.sub(r'\.hub-card:hover\s*\{[^}]*\}', '', html) # Remove old hover rule
    print("✅ Fixed: Main hub boxes upgraded with premium depth and brand borders.")

    # ==========================================
    # 3. CLEAN UP & ENHANCE DIRECTORY BOXES
    # ==========================================
    # Step A: Strip the messy inline styles from the directory cards
    html = re.sub(r'(class="directory-card")\s+style="[^"]*"', r'\1', html)
    
    # Step B: Inject clean, global CSS for the directory cards into the <style> block
    directory_card_css = """
        /* Modern Directory Cards */
        .directory-card {
            background: #ffffff;
            border: 1px solid #e2e8f0 !important;
            padding: 16px 20px;
            border-radius: 8px;
            text-decoration: none;
            color: #333;
            display: block;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: all 0.2s ease;
        }
        .directory-card:hover {
            border-color: #0056b3 !important;
            background: #f8fafc !important;
            box-shadow: 0 6px 12px rgba(0,86,179,0.08) !important;
            transform: translateY(-2px);
        }
    </style>"""
    
    # Replace the old directory hover CSS and closing style tag with our new comprehensive CSS
    html = re.sub(r'\/\*\s*Directory cards hover\s*\*\/[\s\S]*?\.directory-card:hover\s*\{[^}]*\}', '', html)
    if '/* Modern Directory Cards */' not in html:
        html = html.replace('</style>', directory_card_css)
    
    print("✅ Fixed: Directory boxes stripped of inline styles and given clean UI states.")

    # Save the polished HTML
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print("\n🏁 UI Polish Complete. The hero text is now legible and boxes look highly clickable.")

if __name__ == "__main__":
    polish_homepage_ui(os.getcwd())