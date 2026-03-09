import glob
import re

def fix_duplicate_english_iep_cards():
    """
    Scans all NYC district index.html files and removes the broken 
    English 'What is an IEP' hub card (the one with the descriptor), 
    while leaving the Spanish card and the correct English card untouched.
    """
    # Target all NYC district hub pages
    search_path = 'districts/nyc-district-*/index.html'
    files = glob.glob(search_path)
    
    # REGEX EXPLANATION:
    # Matches: <a class="hub-card" ...>
    # Where href contains exactly: "what-is-an-iep-" followed by anything then ".html"
    # The trailing hyphen ensures "what-is-an-iep.html" is IGNORED.
    # It does not look for "que-es-un-iep", so Spanish is IGNORED.
    pattern = re.compile(
        r'<a class="hub-card"[^>]*href="[^"]*what-is-an-iep-[^"]*\.html"[^>]*>.*?</a>', 
        re.IGNORECASE | re.DOTALL
    )
    
    count = 0
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Perform the replacement, storing the new content and how many replacements were made
        new_content, num_replacements = pattern.subn('', content)
        
        # If a broken card was found and removed, save the file
        if num_replacements > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed: {file_path} (Removed {num_replacements} broken English card)")
            count += 1
            
    print(f"\n✅ Done! Cleaned up broken English IEP cards across {count} NYC district hubs.")

if __name__ == '__main__':
    fix_duplicate_english_iep_cards()