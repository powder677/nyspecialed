import os
import re

# Define our directories
ES_DIR = "./districts/"
EN_DIR = "./districts/"

if not os.path.exists(ES_DIR):
    print(f"Could not find the {ES_DIR} folder. Make sure you are in the root directory.")
    exit()

# Get all the English district folders
en_folders = [f for f in os.listdir(EN_DIR) if os.path.isdir(os.path.join(EN_DIR, f))]
files_moved = 0

print("Starting Spanish file migration...")

for es_folder in os.listdir(ES_DIR):
    es_path = os.path.join(ES_DIR, es_folder)
    if not os.path.isdir(es_path):
        continue

    # Extract the district ID (e.g., 'nyc-district-01')
    match = re.match(r'(nyc-district-\d+)', es_folder)
    if not match:
        continue
    
    dist_prefix = match.group(1)
    
    # Find the corresponding English folder
    en_target = next((f for f in en_folders if f.startswith(dist_prefix)), None)
    
    if en_target:
        target_path = os.path.join(EN_DIR, en_target)
        
        for file in os.listdir(es_path):
            if file.endswith('.html'):
                src_file = os.path.join(es_path, file)
                dst_file = os.path.join(target_path, file)
                
                # Read the Spanish file
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 1. Fix CSS/JS Depth (from 3 folders deep to 2 folders deep)
                content = content.replace('../../../', '../../')
                
                # 2. Fix the `../` hub links that caused those 113 errors in our audit
                # This points the "Back" button to the main English Districts hub
                content = re.sub(r'href=(["\'])\.\./\1', r'href=\1../index.html\1', content)
                
                # Write the new file to the English folder
                with open(dst_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Migrated: {file} -> /districts/{en_target}/")
                files_moved += 1

print(f"\nMigration complete! Successfully integrated {files_moved} Spanish files.")
print("You can now safely delete the old '/es/' folder if you no longer need it.")