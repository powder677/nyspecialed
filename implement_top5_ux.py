import os
import re

def fix_ui_ux(root_dir):
    index_path = os.path.join(root_dir, 'index.html')
    css_path = os.path.join(root_dir, 'styles', 'global.css')
    
    print("🚀 Initiating Top 5 UX/UI Fixes...")

    # ==========================================
    # FIX 4: Typography Accessibility (CSS)
    # ==========================================
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        
        # Find .d-desc and update font-size to 1rem and add line-height
        css = re.sub(
            r'(\.d-desc\s*\{[^\}]*?font-size:\s*)0\.85rem',
            r'\g<1>1rem;\n  line-height: 1.5;\n  color: #475569',
            css
        )
        # Strip out the old color rule if it duplicated
        css = re.sub(r'color:\s*#666;(?=\s*\})', '', css)
        
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css)
        print("✅ Fix 4 Applied: Typography Accessibility updated in global.css")
    else:
        print(f"⚠️ CSS file not found at {css_path}")

    # ==========================================
    # HTML INJECTIONS (index.html)
    # ==========================================
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # FIX 1: Add Primary Hero CTA
        if 'class="hero-cta"' not in html:
            html = html.replace(
                '<div style="height: 50px;"></div>\n    </header>',
                '<div style="margin-top: 40px; margin-bottom: 20px;">\n            <a href="/guides/cse-meeting-guide" class="hero-cta">Start the Free CSE Guide</a>\n        </div>\n        <div style="height: 50px;"></div>\n    </header>'
            )
            print("✅ Fix 1 Applied: Hero CTA injected below stats bar.")

        # FIX 5: Semantic HTML <main> Landmark
        if '<main id="main-content">' not in html:
            html = html.replace('<div class="main-hub-grid">', '<main id="main-content">\n    <div class="main-hub-grid">')
            html = html.replace('</section>\n\n<footer class="site-footer"', '</section>\n</main>\n\n<footer class="site-footer"')
            print("✅ Fix 5 Applied: Semantic <main> tags wrapped around core content.")

        # FIX 3: Add Lead Magnet Section
        lead_magnet = """
    <section class="lead-magnet" style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 60px 20px; border-bottom: 1px solid #cbd5e1; margin-top: 20px;">
        <div class="container" style="max-width: 800px; margin: 0 auto; text-align: center;">
            <h2 style="color: #002868; font-size: 2.2rem; margin-bottom: 15px;"><i class="fas fa-file-pdf" style="color: #c8102e; margin-right: 10px;"></i> Get the NY IEP Meeting Checklist</h2>
            <p style="font-size: 1.1rem; color: #475569; margin-bottom: 30px;">Don't walk into your CSE meeting unprepared. Download our free, step-by-step checklist to ensure your child's rights are legally protected.</p>
            
            <form action="#" method="POST" style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; max-width: 600px; margin: 0 auto;">
                <input type="email" placeholder="Enter your best email address" required aria-label="Email Address" style="flex: 1; min-width: 250px; padding: 15px 20px; border: 2px solid #cbd5e1; border-radius: 50px; font-size: 1rem; outline: none; transition: border-color 0.2s;">
                <button type="submit" class="button-primary" style="padding: 15px 35px; font-size: 1.1rem; white-space: nowrap; box-shadow: 0 4px 6px rgba(200, 16, 46, 0.2);">Send Checklist Now</button>
            </form>
            <p style="font-size: 0.85rem; color: #64748b; margin-top: 15px;"><i class="fas fa-lock"></i> 100% Secure. We never share your data.</p>
        </div>
    </section>
"""
        if 'class="lead-magnet"' not in html:
            html = html.replace(
                '</section>\n\n\n    <section id="directory"',
                f'</section>\n{lead_magnet}\n    <section id="directory"'
            )
            print("✅ Fix 3 Applied: Lead Magnet email capture section inserted.")

        # FIX 2: Condense the Directory into Accordions
        # This regex safely identifies the <h3> region titles and their subsequent grid of links
        def wrap_accordion(match):
            h3 = match.group(1)
            grid = match.group(2)
            
            # Strip out inline styles from the h3 that conflict with our new flexbox summary layout
            h3_clean = re.sub(r'margin-top:\s*[^;]+;?', '', h3)
            h3_clean = re.sub(r'border-bottom:\s*[^;]+;?', '', h3_clean)
            h3_clean = re.sub(r'padding-bottom:\s*[^;]+;?', '', h3_clean)
            
            return f'''
        <details class="district-accordion" style="margin-bottom: 1rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <summary style="cursor: pointer; padding: 15px 20px; background: #f8fafc; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; list-style: none;">
                <div style="pointer-events: none; margin: 0; padding: 0;">{h3_clean}</div>
                <span style="font-size: 0.9rem; font-weight: 600; color: #0056b3; background: #e0f2fe; padding: 6px 12px; border-radius: 20px; border: 1px solid #bae6fd;">Expand <i class="fas fa-chevron-down" style="margin-left: 5px;"></i></span>
            </summary>
            <div style="padding: 20px; background: #ffffff;">
                {grid}
            </div>
        </details>'''

        accordion_pattern = re.compile(r'(<h3[^>]*>.*?</h3>)\s*(<div class="directory-grid"[^>]*>.*?</div>)', re.DOTALL | re.IGNORECASE)
        
        if '<details class="district-accordion"' not in html:
            html = accordion_pattern.sub(wrap_accordion, html)
            
            # Hide default HTML details marker (arrow) to use our custom UI
            if '::-webkit-details-marker' not in html:
                html = html.replace('</style>', '  details > summary::-webkit-details-marker { display: none; }\n    </style>')
            print("✅ Fix 2 Applied: Directory links condensed into interactive accordions.")

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("\n🏁 All 5 high-priority UX/UI fixes successfully implemented!")

if __name__ == "__main__":
    fix_ui_ux(os.getcwd())