import os
import re

# The folder where your New York HTML files live
FOLDER_PATH = "." 

def replace_bot_with_link(directory):
    files_fixed = 0
    
    # We use a Regular Expression to find the entire sidebar block, 
    # no matter how the spaces or line breaks are formatted in each file.
    bot_pattern = re.compile(
        r'<div class="premium-sidebar-right"[^>]*>\s*<div id="iep-bot-sidebar"[\s\S]*?<iframe[\s\S]*?</iframe>\s*</div>\s*</div>',
        re.IGNORECASE | re.DOTALL
    )

    # The clean, fast-loading sidebar card that links to your bot page
    new_sidebar = """<div class="premium-sidebar-right" style="flex: 1 1 30%; min-width: 300px; position: sticky; top: 20px;">
  <div style="background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.08);">
    <div style="background: #2d5248; padding: 36px 24px; text-align: center; color: white;">
      <h3 style="margin: 0 0 12px 0; font-family: 'Lora', serif; font-size: 24px;">IEP Letter Writer</h3>
      <p style="margin: 0 0 24px 0; font-size: 15px; color: #e2e8f0; line-height: 1.6;">Don't know what to say to the CSE? Let our AI bot generate a custom, legally-sound request letter for you in minutes.</p>
      <a href="/tools/" style="display: inline-block; background: #c9973a; color: #2d5248; font-weight: 800; padding: 14px 24px; border-radius: 6px; text-decoration: none; font-size: 15px; box-shadow: 0 4px 12px rgba(201, 151, 58, 0.3);">Open Letter Writer →</a>
    </div>
  </div>
</div>"""

    print("🔍 Scanning New York site to replace bots with links...")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # If we find the bot iframe, swap it out!
                    if bot_pattern.search(content):
                        new_content = bot_pattern.sub(new_sidebar, content)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        files_fixed += 1
                        print(f"✅ Replaced Bot in: {filepath}")
                except Exception as e:
                    print(f"⚠️ Could not read {filepath}: {e}")

    print(f"\n🎉 Done! Successfully removed the bot and added links on {files_fixed} pages.")

if __name__ == "__main__":
    replace_bot_with_link(FOLDER_PATH)