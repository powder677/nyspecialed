import os
import re

BASE_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"

# Regex patterns
DISTRICT_PAGE_PATTERN = re.compile(
    r'href="(/districts/[^"/]+/([^"/]+)/)"'
)

DISTRICT_ROOT_PATTERN = re.compile(
    r'href="(/districts/[^"/]+/)"'
)


def fix_links_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Convert subpages to .html
    content = DISTRICT_PAGE_PATTERN.sub(
        lambda m: f'href="{m.group(1)}{m.group(2)}.html"',
        content
    )

    # Convert district root to index.html
    content = DISTRICT_ROOT_PATTERN.sub(
        lambda m: f'href="{m.group(1)}index.html"',
        content
    )

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    return False


def run():
    changed_files = []

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                if fix_links_in_file(filepath):
                    changed_files.append(filepath)

    print("\n=== LINK FIX REPORT ===")
    print(f"Total files modified: {len(changed_files)}")
    for f in changed_files:
        print(f"✔ Fixed: {f}")


if __name__ == "__main__":
    run()