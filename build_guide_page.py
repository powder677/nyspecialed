import os

def fix_guide_page(root_dir):
    guide_path = os.path.join(root_dir, 'guides', 'cse-meeting-guide', 'index.html')
    nav_path = os.path.join(root_dir, 'components', 'components-navbar.html')
    footer_path = os.path.join(root_dir, 'components', 'components-footer.html')

    if not os.path.exists(guide_path):
        print(f"⚠️ Guide not found at {guide_path}")
        return

    # 1. Read the raw text fragment
    with open(guide_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Safety check: If it already has an HTML shell, abort so we don't break it
    if "<!DOCTYPE html>" in content or "<head>" in content:
        print("⚠️ File already has an HTML shell. Aborting to prevent double-wrapping.")
        return

    print("🚀 Rebuilding CSE Meeting Guide with Navigation and Footer...")

    # 2. Fetch the global Navbar and Footer
    navbar = ""
    if os.path.exists(nav_path):
        with open(nav_path, 'r', encoding='utf-8') as f:
            navbar = f.read()
    else:
        print(f"⚠️ Could not find {nav_path}. Skipping Nav.")

    footer = ""
    if os.path.exists(footer_path):
        with open(footer_path, 'r', encoding='utf-8') as f:
            footer = f.read()
    else:
        print(f"⚠️ Could not find {footer_path}. Skipping Footer.")

    # 3. Construct the premium, highly-readable layout
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New York State CSE Meeting Guide | New York Special Ed</title>
    <meta name="description" content="A comprehensive parent guide to navigating the Committee on Special Education (CSE) meetings in New York State.">
    
    <link rel="stylesheet" href="/styles/global.css">
    <link rel="stylesheet" href="/styles/styles-nav-footer.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        body {{ background: #f8fafc; }}
        
        .guide-wrapper {{
            max-width: 850px;
            margin: 40px auto 80px auto;
            padding: 50px 60px;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            border-top: 5px solid #c8102e; /* Brand Red Anchor */
        }}
        
        .guide-wrapper h1 {{
            color: #002868;
            font-size: 2.8rem;
            font-weight: 800;
            margin-bottom: 20px;
            line-height: 1.2;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 15px;
        }}
        
        .guide-wrapper h2 {{
            color: #002868;
            font-size: 1.8rem;
            margin-top: 40px;
            margin-bottom: 15px;
        }}
        
        .guide-wrapper p {{
            font-size: 1.15rem;
            line-height: 1.7;
            color: #334155;
            margin-bottom: 20px;
        }}
        
        .guide-wrapper ul, .guide-wrapper ol {{
            margin-bottom: 25px;
            padding-left: 20px;
        }}
        
        .guide-wrapper li {{
            font-size: 1.1rem;
            line-height: 1.6;
            color: #334155;
            margin-bottom: 12px;
        }}
        
        .guide-wrapper li b {{
            color: #002868;
        }}
        
        /* Mobile Responsiveness */
        @media (max-width: 768px) {{
            .guide-wrapper {{ padding: 30px 20px; margin: 20px; }}
            .guide-wrapper h1 {{ font-size: 2.2rem; }}
        }}
    </style>
</head>
<body>

    {navbar}

    <main id="main-content">
        <div class="guide-wrapper">
            {content}
        </div>
    </main>

    {footer}

</body>
</html>"""

    # 4. Save the compiled page
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print("✅ Success! The Guide has been upgraded into a full webpage with Navigation, Footer, and Premium Typography.")

if __name__ == "__main__":
    fix_guide_page(os.getcwd())