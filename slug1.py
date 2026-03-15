import os

class DirectoryPatcher:
    def __init__(self, target_file):
        self.target_file = target_file
        self.bad_code = '<a href="/districts/index.html" class="district-card">'
        # Using template literals to dynamically insert the district slug
        self.good_code = '<a href="/districts/${d.slug}/index.html" class="district-card">'

    def patch_js_routing(self):
        if not os.path.exists(self.target_file):
            print(f"Error: {self.target_file} not found.")
            return

        with open(self.target_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if self.bad_code in content:
            print(f"Bad routing found in {self.target_file}. Patching...")
            updated_content = content.replace(self.bad_code, self.good_code)
            
            with open(self.target_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print("Patch successful. District cards will now route to their proper URLs.")
        elif self.good_code in content:
            print("File is already patched.")
        else:
            print("Could not locate the specific anchor tag string. Please check the file manually.")

if __name__ == "__main__":
    # Point to the specific districts/index.html file
    patcher = DirectoryPatcher(target_file="./districts/index.html")
    patcher.patch_js_routing()