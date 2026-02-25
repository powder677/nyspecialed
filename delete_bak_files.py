import os

def delete_bak_files(root_dir):
    deleted_count = 0
    
    print(f"🔍 Scanning directory: {root_dir}")
    print("Looking for .bak files to delete...\n")

    # Walk through all directories and subdirectories
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".bak"):
                filepath = os.path.join(dirpath, filename)
                try:
                    os.remove(filepath)
                    print(f"🗑️ Deleted: {filepath}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Failed to delete {filepath}: {e}")

    print(f"\n✅ Cleanup Complete. Successfully deleted {deleted_count} .bak files.")

if __name__ == "__main__":
    # Ensure this runs in the current working directory
    current_directory = os.getcwd()
    
    # SAFETY PROMPT: Just in case it's run in the wrong place
    confirm = input(f"⚠️ You are about to delete all .bak files in:\n{current_directory}\nProceed? (y/n): ")
    
    if confirm.lower() == 'y':
        delete_bak_files(current_directory)
    else:
        print("🛑 Operation cancelled.")