import os
import re

def fix_guide_blue_on_blue(root_dir):
    print("🚀 Deploying Blue-on-Blue Hotfix for Guide Pages...")
    guides_dir = os.path.join(root_dir, 'guides')
    
    if not os.path.exists(guides_dir):
        print(f"⚠️ Could not find guides directory at {guides_dir}")
        return

    modified_count = 0
    
    # Loop through all sub-directories in /guides/
    for item in os.listdir(guides_dir):
        sub_dir = os.path.join(guides_dir, item)
        if os.path.isdir(sub_dir):
            index_path = os.path.join(sub_dir, 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                    
                orig_html = html
                
                # 1. Downgrade the aggressive dark blue rule so the cascade works properly
                html = html.replace('color: #002868 !important;', 'color: #002868;')
                
                # 2. Inject an absolute bulletproof override for ANY hero section inside a guide
                hero_override = """
        /* Bulletproof Hero Contrast Override */
        .guide-wrapper .hero-section {
            border-radius: 8px; /* Makes it look nice if constrained in the wrapper */
            margin-bottom: 30px;
        }
        .guide-wrapper .hero-section h1, 
        .guide-wrapper .hero-section h2, 
        .guide-wrapper .hero-section p,
        .guide-wrapper .hero-title { 
            color: #ffffff !important; 
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
    </style>"""
                
                # Apply the override right before the closing style tag
                if '/* Bulletproof Hero Contrast Override */' not in html:
                    html = html.replace('</style>', hero_override)
                
                # Save changes
                if html != orig_html:
                    with open(index_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    modified_count += 1
                    
    print(f"✅ Success! Patched {modified_count} guide pages. Hero text is now forced white.")

if __name__ == "__main__":
    fix_guide_blue_on_blue(os.getcwd())