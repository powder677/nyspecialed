import os
import re

def fix_index_page(root_dir):
    index_path = os.path.join(root_dir, 'index.html')
    if not os.path.exists(index_path):
        print(f"⚠️ Could not find {index_path}")
        return

    print("🚀 Initiating Final Homepage Rebuild...")

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # ==========================================
    # 1. FIX THE STRETCHING BUG (Force items to top)
    # ==========================================
    html = re.sub(
        r'(class="directory-grid"\s+style="[^"]*)(")',
        r'\1; align-items: start;\2',
        html
    )

    # ==========================================
    # 2. IMPLEMENT INTERACTIVE ACCORDIONS
    # ==========================================
    def accordion_replacer(match):
        title_html = match.group(1)
        grid_html = match.group(2)
        
        # Clean up old title inline styles that conflict with flexbox
        clean_title = re.sub(r'style="[^"]*"', '', title_html)
        
        return f'''
        <details class="district-accordion" style="margin-bottom: 1rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <summary style="cursor: pointer; padding: 15px 20px; background: #f8fafc; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; list-style: none; font-weight: bold; font-size: 1.1rem; color: #002868;">
                <div style="pointer-events: none;">{clean_title}</div>
                <span style="font-size: 0.85rem; font-weight: bold; color: #0056b3; background: #e0f2fe; padding: 6px 12px; border-radius: 20px; border: 1px solid #bae6fd;">View <i class="fas fa-chevron-down" style="margin-left: 5px;"></i></span>
            </summary>
            <div style="padding: 20px; background: #ffffff;">
                {grid_html}
            </div>
        </details>'''
    
    # Safely target any <h3> immediately followed by a directory grid
    accordion_pattern = re.compile(r'(<h3[^>]*>.*?</h3>)\s*(<div class="directory-grid"[^>]*>.*?</div>)', re.DOTALL | re.IGNORECASE)
    html = accordion_pattern.sub(accordion_replacer, html)

    # ==========================================
    # 3. FIX HERO TEXT CONTRAST & ADD CTA
    # ==========================================
    hero_css = """
        .hero-title {
            font-size: 3rem;
            margin-bottom: 20px;
            font-weight: 800;
            color: #ffffff; /* Forces text to high-contrast white */
            text-shadow: 0 2px 4px rgba(0,0,0,0.4);
        }
        details > summary::-webkit-details-marker { display: none; } /* Hides default arrow */
    """
    html = re.sub(r'\.hero-title\s*\{[^}]*\}', hero_css.strip(), html)

    if 'class="hero-cta"' not in html:
        html = html.replace(
            '<div style="height: 50px;"></div>\n    </header>',
            '<div style="margin-top: 40px; margin-bottom: 20px;">\n            <a href="/guides/cse-meeting-guide" class="hero-cta">Start the Free CSE Guide</a>\n        </div>\n        <div style="height: 50px;"></div>\n    </header>'
        )

    # ==========================================
    # 4. FIX HUB CARDS (Add red border & lift)
    # ==========================================
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
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .hub-card:hover { 
            transform: translateY(-6px); 
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }"""
    html = re.sub(r'\.hub-card\s*\{[^}]*\}', hub_card_css.strip(), html)
    html = re.sub(r'\.hub-card:hover\s*\{[^}]*\}', '', html)

    # ==========================================
    # 5. CLEAN DIRECTORY STYLES
    # ==========================================
    # Strip messy inline styles from the HTML
    html = re.sub(r'(class="directory-card")\s+style="[^"]*"', r'\1', html)
    
    # Inject clean global CSS for the cards
    card_css = """
        .directory-card {
            background: #ffffff;
            border: 1px solid #e2e8f0 !important;
            padding: 16px 20px;
            border-radius: 8px;
            text-decoration: none;
            color: #333;
            display: block;
            align-self: start; /* Bulletproof anti-stretching */
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
    html = re.sub(r'\/\*\s*Directory cards hover\s*\*\/[\s\S]*?\.directory-card:hover\s*\{[^}]*\}', '', html)
    html = html.replace('</style>', card_css)

    # Save the updated HTML
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Success! Stretching fixed. Accordions applied. Hero text legible.")

if __name__ == "__main__":
    fix_index_page(os.getcwd())