import os
import re

BASE_DIR = r"C:\Users\elisa\OneDrive\Documents\github\nyspecialed"

# Matches: /districts/district/page/page.html
pattern = re.compile(
    r'href="(/districts/([^/]+)/([^/]+)/\3\.html)"'
)

def fix_links(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    content = pattern.sub(
        lambda m: f'href="/districts/{m.group(2)}/{m.group(3)}.html"',
        content
    )

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    return False


def run():
    changed = []

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                if fix_links(filepath):
                    changed.append(filepath)

    print("\n--- FIX REPORT ---")
    print(f"Files updated: {len(changed)}")
    for f in changed:
        print("✔", f)


if __name__ == "__main__":
    run()