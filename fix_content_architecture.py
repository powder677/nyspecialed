import os
import re

def fix_architecture_and_styling(root_dir):
    print("🚀 Initiating Site-Wide Architecture & Styling Fix...")

    # ==========================================
    # 1. FIX GLOBAL "BLUE ON BLUE" BUG
    # ==========================================
    css_path = os.path.join(root_dir, 'styles', 'global.css')
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        
        # Inject an absolute override for any h1 or title inside a hero section
        if '/* HERO TEXT OVERRIDE */' not in css:
            css += "\n\n/* HERO TEXT OVERRIDE */\n.hero-section h1, .hero-title, .hero-section h2, .hero-section p { color: #ffffff !important; text-shadow: 0 2px 4px rgba(0,0,0,0.4); }\n"
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css)
            print("✅ Global CSS Fixed: Blue-on-Blue bug eliminated permanently.")

    # Fetch global components
    nav_path = os.path.join(root_dir, 'components', 'components-navbar.html')
    footer_path = os.path.join(root_dir, 'components', 'components-footer.html')
    navbar = open(nav_path, 'r', encoding='utf-8').read() if os.path.exists(nav_path) else ""
    footer = open(footer_path, 'r', encoding='utf-8').read() if os.path.exists(footer_path) else ""

    # Premium Reading Layout CSS
    guide_style = """
    <style>
        body { background: #f8fafc; }
        .guide-wrapper { max-width: 850px; margin: 40px auto 80px auto; padding: 50px 60px; background: #ffffff; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-top: 5px solid #c8102e; }
        .guide-wrapper h1 { color: #002868 !important; font-size: 2.8rem; font-weight: 800; margin-bottom: 20px; line-height: 1.2; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; }
        .guide-wrapper h2 { color: #002868 !important; font-size: 1.8rem; margin-top: 40px; margin-bottom: 15px; }
        .guide-wrapper p, .guide-wrapper li { font-size: 1.15rem; line-height: 1.7; color: #334155; }
        .guide-wrapper ul, .guide-wrapper ol { margin-bottom: 25px; padding-left: 20px; }
        .guide-wrapper li { margin-bottom: 12px; }
        .guide-wrapper li b { color: #002868; }
        @media (max-width: 768px) { .guide-wrapper { padding: 30px 20px; margin: 20px; } .guide-wrapper h1 { font-size: 2.2rem; } }
    </style>
    """

    # ==========================================
    # 2. WRAP ALL NAKED GUIDE PAGES
    # ==========================================
    guides_dir = os.path.join(root_dir, 'guides')
    if os.path.exists(guides_dir):
        for item in os.listdir(guides_dir):
            sub_dir = os.path.join(guides_dir, item)
            if os.path.isdir(sub_dir):
                index_path = os.path.join(sub_dir, 'index.html')
                if os.path.exists(index_path):
                    with open(index_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # If it's a raw text file lacking HTML tags, wrap it in our premium UI
                    if "<!DOCTYPE html>" not in content:
                        title = item.replace('-', ' ').title()
                        full_html = f"""<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{title} | NY Special Ed</title>\n    <link rel="stylesheet" href="/styles/global.css">\n    <link rel="stylesheet" href="/styles/styles-nav-footer.css">\n    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">\n{guide_style}\n</head>\n<body>\n{navbar}\n    <main id="main-content">\n        <div class="guide-wrapper">\n{content}\n        </div>\n    </main>\n{footer}\n</body>\n</html>"""
                        with open(index_path, 'w', encoding='utf-8') as f:
                            f.write(full_html)
                        print(f"✅ Wrapped naked text content in: /guides/{item}")

    # ==========================================
    # 3. REBUILD THE GUIDES HUB DIRECTORY
    # ==========================================
    guides_hub = os.path.join(guides_dir, 'index.html')
    hub_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Special Education Guides | NY Special Ed</title>
    <link rel="stylesheet" href="/styles/global.css">
    <link rel="stylesheet" href="/styles/styles-nav-footer.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .hero-section {{ background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 80px 20px; text-align: center; }}
        .hero-title {{ font-size: 3rem; font-weight: 800; color: #ffffff !important; text-shadow: 0 2px 4px rgba(0,0,0,0.4); margin-bottom: 20px; }}
        .hub-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; max-width: 1100px; margin: -40px auto 60px auto; padding: 0 20px; position: relative; z-index: 2; }}
        .hub-card {{ background: white; padding: 30px; border: 1px solid #e2e8f0; border-top: 4px solid #c8102e; border-radius: 12px; text-decoration: none; color: inherit; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); transition: transform 0.2s ease, box-shadow 0.2s ease; display: flex; flex-direction: column; }}
        .hub-card:hover {{ transform: translateY(-6px); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); border-color: #0056b3; }}
        .hub-card h3 {{ color: #002868; font-size: 1.4rem; margin-top: 0; margin-bottom: 10px; }}
        .hub-card p {{ color: #475569; line-height: 1.5; margin-bottom: 0; }}
        .hub-icon {{ font-size: 2rem; color: #c8102e; margin-bottom: 15px; }}
    </style>
</head>
<body style="background: #f8fafc;">
    {navbar}
    <main id="main-content">
        <header class="hero-section">
            <h1 class="hero-title">NY Special Education Guides</h1>
            <p style="color: #e2e8f0; font-size: 1.2rem; max-width: 600px; margin: 0 auto;">Comprehensive, easy-to-understand resources for navigating your child's rights.</p>
        </header>
        <div class="hub-grid">
            <a href="/guides/cse-meeting-guide" class="hub-card"><i class="fas fa-users hub-icon"></i><h3>CSE Meeting Guide</h3><p>Master the Annual Review and Initial Eligibility meetings.</p></a>
            <a href="/guides/evaluation-request-ny" class="hub-card"><i class="fas fa-file-signature hub-icon"></i><h3>Requesting an Evaluation</h3><p>Step-by-step instructions on initiating the 60-day timeline.</p></a>
            <a href="/guides/dispute-resolution-ny" class="hub-card"><i class="fas fa-balance-scale hub-icon"></i><h3>Dispute Resolution</h3><p>Mediation, Impartial Hearings, and state complaints.</p></a>
            <a href="/guides/cpse-preschool-special-education" class="hub-card"><i class="fas fa-child hub-icon"></i><h3>CPSE (Preschool Services)</h3><p>Navigating the Committee on Preschool Special Education.</p></a>
            <a href="/guides/bilingual-iep-new-york" class="hub-card"><i class="fas fa-language hub-icon"></i><h3>Bilingual & ELL Rights</h3><p>Securing bilingual assessments and native language support.</p></a>
            <a href="/guides/carter-cases-private-placement" class="hub-card"><i class="fas fa-school hub-icon"></i><h3>Private Placement (Carter Cases)</h3><p>Seeking district funding for private school tuition.</p></a>
        </div>
    </main>
    {footer}
</body>
</html>"""
    with open(guides_hub, 'w', encoding='utf-8') as f:
        f.write(hub_html)
    print("✅ Rebuilt Guides Directory Hub (guides/index.html) with premium links.")

    # ==========================================
    # 4. FORMAT RESOURCES PAGE
    # ==========================================
    res_dir = os.path.join(root_dir, 'resources')
    res_index = os.path.join(res_dir, 'index.html')
    if os.path.exists(res_index):
        with open(res_index, 'r', encoding='utf-8') as f:
            res_content = f.read()
        
        # Wrap raw resources in a stylized container
        if "<!DOCTYPE html>" not in res_content:
            res_html = f"""<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Parent Resources | NY Special Ed</title>\n    <link rel="stylesheet" href="/styles/global.css">\n    <link rel="stylesheet" href="/styles/styles-nav-footer.css">\n    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">\n{guide_style}\n</head>\n<body>\n{navbar}\n    <main id="main-content">\n        <header class="hero-section" style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 60px 20px; text-align: center;">\n            <h1 class="hero-title" style="color: white !important;">NY Special Education Resources</h1>\n            <p style="color: #e2e8f0; font-size: 1.2rem; max-width: 600px; margin: 0 auto;">Templates, tools, and external links to empower your advocacy.</p>\n        </header>\n        <div class="guide-wrapper" style="margin-top: -30px; position: relative; z-index: 2;">\n{res_content}\n        </div>\n    </main>\n{footer}\n</body>\n</html>"""
            with open(res_index, 'w', encoding='utf-8') as f:
                f.write(res_html)
            print("✅ Wrapped and formatted Resources page.")

    print("🏁 Batch Processing Complete! Architecture and formatting restored.")

if __name__ == "__main__":
    fix_architecture_and_styling(os.getcwd())