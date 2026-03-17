import os

# Set this to the folder where your New York HTML files live
FOLDER_PATH = "." 

def fix_ny_html(directory):
    files_fixed = 0
    
    # The block of code we are looking for
    old_text = """            const signupData = {
                email: email,
                source: 'newsletter_popup',"""
    
    # The new block of code specifically for New York
    new_text = """            const signupData = {
                email: email,
                site: 'new_york_special_ed',
                language: 'en',
                source: 'newsletter_popup',"""

    print("🔍 Scanning New York site for HTML files to fix...")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if old_text in content:
                        new_content = content.replace(old_text, new_text)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        files_fixed += 1
                        print(f"✅ Fixed (New York): {filepath}")
                except Exception as e:
                    print(f"⚠️ Could not read {filepath}: {e}")

    print(f"\n🎉 Done! Successfully updated {files_fixed} New York files.")

if __name__ == "__main__":
    fix_ny_html(FOLDER_PATH)