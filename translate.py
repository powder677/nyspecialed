import os
import time
import re
from deep_translator import GoogleTranslator

# Your specific path
GUIDES_DIR = r'C:\Users\elisa\OneDrive\Documents\github\nyspecialed\guides'

def is_markdown_syntax(line):
    """Detects if a line is just Markdown structural symbols."""
    stripped = line.strip()
    if not stripped:
        return True
    # Matches lines like ---, ===, |---|---|, or headers like # 
    if re.match(r'^[=\-\|\s\:\+#]+$', stripped):
        return True
    return False

def translate_blog_posts():
    translator = GoogleTranslator(source='en', target='es')
    
    # The specific filenames for your 6 new blog posts
    filenames = [
        "post-1-cse-meeting-hub-survival-guide.md",
        "post-2-what-is-a-cse-meeting.md",
        "post-3-turning-5-cpse-to-cse-transition.md",
        "post-4-independent-educational-evaluation-iee.md",
        "post-5-carter-cases-unilateral-placement.md",
        "post-6-nyc-special-education-sbst-iesp-june-1.md"
    ]

    for filename in filenames:
        input_path = os.path.join(GUIDES_DIR, filename)
        output_filename = filename.replace(".md", "_es.md")
        output_path = os.path.join(GUIDES_DIR, output_filename)

        if not os.path.exists(input_path):
            print(f"Skipping {filename}: File not found in directory.")
            continue

        print(f"Translating: {filename}...")

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            translated_lines = []
            for line in lines:
                # If it's just Markdown symbols, don't translate it
                if is_markdown_syntax(line):
                    translated_lines.append(line)
                    continue

                # Translate actual text
                try:
                    # Preserve the original indentation (spaces at the start)
                    stripped_text = line.strip()
                    indent = line[:line.find(stripped_text)]
                    
                    translated_text = translator.translate(stripped_text)
                    
                    if translated_text:
                        translated_lines.append(f"{indent}{translated_text}\n")
                    else:
                        translated_lines.append(line)
                        
                    # Small delay to keep the API happy
                    time.sleep(0.1) 
                except Exception:
                    translated_lines.append(line)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(translated_lines)
            
            print(f"Successfully saved to {output_filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    translate_blog_posts()
    print("\n--- Translation of all 6 blogs complete! ---")