import os
import re

def rescue_homepage(root_dir):
    index_path = os.path.join(root_dir, 'index.html')
    
    if not os.path.exists(index_path):
        print(f"⚠️ Could not find {index_path}")
        return

    print("🚀 Deploying Homepage Rescue Script...")

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # ==========================================
    # 1. FIX THE MANHATTAN ACCORDION CORRUPTION
    # ==========================================
    bad_manhattan = r'<div class="borough-section"><h3 class="borough-title"[^>]*><i class="fas fa-map-marker-alt"></i> Manhattan</h3></div>\s*<span[^>]*>Expand.*?</span>\s*</summary>'
    good_manhattan = '''<details class="district-accordion" style="margin-bottom: 1rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <summary style="cursor: pointer; padding: 15px 20px; background: #f8fafc; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; list-style: none;">
                <div style="pointer-events: none; margin: 0; padding: 0; font-size: 1.15rem; font-weight: bold; color: #002868;"><i class="fas fa-map-marker-alt"></i> Manhattan</div>
                <span style="font-size: 0.9rem; font-weight: 600; color: #0056b3; background: #e0f2fe; padding: 6px 12px; border-radius: 20px; border: 1px solid #bae6fd;">Expand <i class="fas fa-chevron-down" style="margin-left: 5px;"></i></span>
            </summary>'''
    html = re.sub(bad_manhattan, good_manhattan, html)

    # ==========================================
    # 2. FIX THE CSE GUIDE HUB CARD CORRUPTION
    # ==========================================
    bad_hub = r'<a href="/guides/cse-meeting-guide/" class="hub-card">\s*<details class="district-accordion"[^>]*>\s*<summary[^>]*>\s*<div[^>]*><h3[^>]*>🤝 CSE Meeting Guide</h3>\s*<p>Master the Annual Review\.'
    good_hub = '''<a href="/guides/cse-meeting-guide/" class="hub-card">
            <h3 style="color: #c8102e; margin-top: 0; margin-bottom: 10px;">🤝 CSE Meeting Guide</h3>
            <p style="margin: 0; color: #475569;">Master the Annual Review.'''
    html = re.sub(bad_hub, good_hub, html)

    # ==========================================
    # 3. STRIP INLINE STYLES FROM SPANS
    # ==========================================
    # This allows the CSS to actually control the text rendering
    html = re.sub(r'<span class="d-name" style="[^"]*">', r'<span class="d-name">', html)
    html = re.sub(r'<span class="d-desc" style="[^"]*">', r'<span class="d-desc">', html)

    # ==========================================
    # 4. INJECT PRISTINE CSS BLOCK
    # ==========================================
    # Wipe the messy duplicate styles and insert the perfectly tuned layout
    clean_style = """<style>
        /* Homepage Specific Styles */
        .hero-section {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
            color: white;
            padding: 80px 20px;
            text-align: center;
        }
        .hero-title {
            font-size: 3rem;
            margin-bottom: 20px;
            font-weight: 800;
            color: #ffffff;
            text-shadow: 0 2px 4px rgba(0,0,0,0.4);
        }
        .hero-subtitle {
            font-size: 1.2rem;
            max-width: 600px;
            margin: 0 auto 30px auto;
            color: #e2e8f0;
        }
        .hero-cta {
            background: #d4af37;
            color: #0f172a;
            padding: 15px 30px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            font-size: 1.1rem;
            display: inline-block;
            transition: transform 0.2s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .hero-cta:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.3); }
        
        .directory-section { padding: 60px 20px; background: #f8f9fa; }
        .directory-container { max-width: 1200px; margin: 0 auto; }
        
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 40px;
            flex-wrap: wrap;
        }
        .stat-item { text-align: center; }
        .stat-num { display: block; font-size: 2.5rem; font-weight: 800; color: #d4af37; }
        .stat-label { color: #e2e8f0; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }

        /* Main Hub Grid */
        .main-hub-grid {
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin: -40px auto 40px auto; 
            max-width: 1100px;
            position: relative;
            z-index: 2;
            padding: 0 20px;
        }
        .hub-card {
            background: white;
            padding: 30px 25px; 
            border: 1px solid #e2e8f0; 
            border-top: 4px solid #c8102e;
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
        }

        /* --- PREMIUM FLEXBOX DIRECTORY CARDS --- */
        details > summary::-webkit-details-marker { display: none; }
        
        .directory-grid {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            max-width: 1100px;
            margin: 10px auto 0 auto;
            align-items: stretch; /* Forces cards in the same row to be identical height */
        }

        .directory-card {
            flex: 1 1 300px;
            max-width: 340px;
            background: #ffffff;
            border-radius: 12px;
            padding: 24px 20px;
            text-align: center;
            text-decoration: none;
            display: flex;
            flex-direction: column;
            justify-content: center; /* Vertically centers the text inside the card */
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }

        .directory-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0,86,179,0.12);
            border-color: #0056b3;
        }
        
        .directory-card .d-name {
            display: block;
            font-size: 1.25rem;
            color: #002868;
            font-weight: 800;
            margin-bottom: 8px;
        }
        
        .directory-card .d-desc {
            font-size: 0.95rem;
            color: #475569;
            line-height: 1.4;
        }
    </style>"""
    
    html = re.sub(r'<style>[\s\S]*?</style>', clean_style, html)

    # Save the rescued HTML
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Success! HTML DOM Corruptions Fixed. Clean CSS Injected.")

if __name__ == "__main__":
    rescue_homepage(os.getcwd())