"""
Replaces the old generic popup with the premium Ink & Gold version
across all HTML files in your NY Special Ed site.

Run from your newyorkspecialed site directory:
  python deploy_premium_popup.py
"""

import os
import glob

POPUP_FILE = os.path.join(os.path.dirname(__file__), "popup-premium.html")

# Markers that identify the old popup block in your HTML files
OLD_POPUP_START = '<div id="ec-overlay"'
OLD_POPUP_END   = "</script>\n</body>"
OLD_POPUP_END_ALT = "</script>\n\n</body>"

def load_new_popup():
    with open(POPUP_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def fix_file(filepath, new_popup):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    if OLD_POPUP_START not in original:
        return False  # no popup in this file

    # Find start of old popup
    start_idx = original.find(OLD_POPUP_START)

    # Find end — the closing </script> just before </body>
    end_idx = -1
    for end_marker in [OLD_POPUP_END_ALT, OLD_POPUP_END]:
        idx = original.find(end_marker, start_idx)
        if idx != -1:
            end_idx = idx + len(end_marker)
            break

    if end_idx == -1:
        # Fallback: find </body> and replace everything before it
        end_idx = original.rfind("</body>")
        if end_idx == -1:
            return False

    updated = original[:start_idx] + new_popup + "\n</body>\n</html>\n"

    if updated != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated)
        return True

    return False

def main():
    if not os.path.exists(POPUP_FILE):
        print(f"ERROR: popup-premium.html not found at {POPUP_FILE}")
        print("Make sure popup-premium.html is in the same folder as this script.")
        return

    html_files = glob.glob("**/*.html", recursive=True)
    if not html_files:
        html_files = glob.glob("*.html")

    if not html_files:
        print("No HTML files found.")
        print(f"Current directory: {os.getcwd()}")
        return

    new_popup = load_new_popup()
    print(f"Scanning {len(html_files)} HTML files...")

    fixed   = 0
    skipped = 0

    for filepath in html_files:
        result = fix_file(filepath, new_popup)
        if result:
            fixed += 1
            if fixed <= 5:
                print(f"  ✓ {filepath}")
        else:
            skipped += 1

    if fixed > 5:
        print(f"  ... and {fixed - 5} more files")

    print(f"\nDone.")
    print(f"  Updated : {fixed} files")
    print(f"  Skipped : {skipped} files (no popup found)")

    if fixed > 0:
        print("\nNext — push to Vercel:")
        print('  git add .')
        print('  git commit -m "Deploy premium Ink & Gold popup"')
        print('  git push')
    else:
        print("\nNo files updated — the old popup markers weren't found.")
        print("Check that you're running this from your newyorkspecialed site folder.")

if __name__ == "__main__":
    main()
