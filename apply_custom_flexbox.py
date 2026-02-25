import os
import re

def apply_user_flexbox(root_dir):
    index_path = os.path.join(root_dir, 'index.html')
    
    if not os.path.exists(index_path):
        print(f"⚠️ Could not find {index_path}")
        return

    print("🚀 Initiating Custom Flexbox UI...")

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # ==========================================
    # 1. STRIP CONFLICTING INLINE STYLES
    # ==========================================
    # Removes style="..." from the grid container so our Flexbox CSS can take over
    html = re.sub(r'(class="directory-grid")\s+style="[^"]*"', r'\1', html)
    # Removes style="..." from the individual cards
    html = re.sub(r'(class="directory-card")\s+style="[^"]*"', r'\1', html)

    # ==========================================
    # 2. INJECT YOUR CUSTOM CSS
    # ==========================================
    user_custom_css = """
        /* --- USER CUSTOM FLEXBOX CARDS --- */
        .directory-grid {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 24px;
            max-width: 1100px;
            margin: 15px auto 0 auto;
            align-items: flex-start; /* Bulletproof anti-stretch */
        }

        .directory-card {
            flex: 1 1 300px;
            max-width: 320px;
            background: #ffffff;
            border-radius: 12px !important;
            padding: 24px !important;
            text-align: center;
            text-decoration: none;
            display: block;
            border: 1px solid #e2e8f0;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
        }

        .directory-card:hover {
            transform: translateY(-6px) !important;
            box-shadow: 0 12px 28px rgba(0,0,0,0.12) !important;
            border-color: #0056b3 !important;
        }
        
        /* Ensure the text inside matches your centered card layout */
        .directory-card .d-name {
            display: block;
            font-size: 1.15rem;
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

    # Remove any old directory hover styles to prevent conflicts
    html = re.sub(r'\/\*\s*Directory cards hover\s*\*\/[\s\S]*?\.directory-card:hover\s*\{[^}]*\}', '', html)
    
    # Inject the new CSS right before the closing style tag
    if '/* --- USER CUSTOM FLEXBOX CARDS --- */' not in html:
        html = html.replace('</style>', user_custom_css)

    # Save the updated HTML
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Success! Stripped old Grid logic and applied your premium Flexbox UI.")

if __name__ == "__main__":
    apply_user_flexbox(os.getcwd())