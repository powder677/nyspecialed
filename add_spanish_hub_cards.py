import os
import glob
import re

def add_spanish_hub_cards():
    """
    Scans all English NYC district hub pages, finds the corresponding 
    Spanish IEP page in the es/distritos/ directory, and injects 
    the Spanish hub card seamlessly into the hub grid.
    """
    # Target all NYC district English hub pages
    english_hubs = glob.glob('districts/nyc-district-*/index.html')
    
    count = 0
    for hub_path in english_hubs:
        # 1. Extract district number (e.g., "01" from "nyc-district-01-lower-east-side")
        match = re.search(r'nyc-district-(\d+)', hub_path)
        if not match:
            continue
        dist_num = match.group(1)
        
        # 2. Find the exact corresponding Spanish file dynamically
        # Pattern looks for: es/distritos/nyc-district-01-*/*.html
        es_pattern = f'es/distritos/nyc-district-{dist_num}-*/*.html'
        es_files = glob.glob(es_pattern)
        
        if not es_files:
            print(f"⚠️ Warning: No Spanish file found for District {dist_num}. Skipping.")
            continue
            
        # Grab the first matching file and format it into a web URL
        es_file_path = es_files[0].replace('\\', '/') # Fix Windows slashes if any
        full_url = f"https://www.newyorkspecialed.net/{es_file_path}"
        
        # 3. Read the English hub page
        with open(hub_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 4. Skip if this exact URL is already in the file to prevent duplicates
        if full_url in content:
            print(f"⏭️ Skipped: District {dist_num} (Spanish card already exists)")
            continue
            
        # First, clean out any lingering old/broken Spanish cards to be safe
        content = re.sub(r'<a class="hub-card"[^>]*>.*?¿Qué Es un IEP.*?</a>', '', content, flags=re.IGNORECASE|re.DOTALL)
        
        # 5. Build the new pristine Spanish Card HTML
        spanish_card = f"""<a class="hub-card" href="{full_url}">
<h3 style="color: #0056b3; margin-top: 0;">🌐 ¿Qué Es un IEP? (Español)</h3>
<p>Guía completa sobre el IEP en el Distrito {dist_num} para familias hispanohablantes.</p>
</a>"""
        
        # 6. Inject the Spanish card directly before the English "What Is an IEP" card
        english_card_pattern = r'(<a class="hub-card" href="[^"]*what-is-an-iep\.html"[^>]*>.*?</a>)'
        
        if re.search(english_card_pattern, content, re.DOTALL):
            new_content = re.sub(
                english_card_pattern, 
                f'{spanish_card}\n\\1', 
                content, 
                flags=re.DOTALL
            )
            
            # Save the file
            with open(hub_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"✅ Added Spanish card to District {dist_num} -> Linked to: {es_file_path}")
            count += 1
        else:
            print(f"⚠️ Warning: Could not find English IEP card in District {dist_num} to anchor next to.")

    print(f"\n🎉 Done! Successfully mapped and injected Spanish cards into {count} NYC district hubs.")

if __name__ == '__main__':
    add_spanish_hub_cards()