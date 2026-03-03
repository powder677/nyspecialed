import os
from bs4 import BeautifulSoup

def update_all_silo_navs(base_dir):
    # Walk through all folders and files in the base directory
    for root, dirs, files in os.walk(base_dir):
        for file_name in files:
            # Target all HTML files (this will catch cse-meeting-guide, evaluation-process, etc.)
            if file_name.endswith('.html'):
                file_path = os.path.join(root, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')

                # Find the district sub-navigation menu
                subnav = soup.find('nav', class_='district-subnav')

                if subnav:
                    # Dynamically determine this specific district's URL base
                    existing_link = subnav.find('a', href=True)
                    if not existing_link:
                        continue
                        
                    base_href = existing_link['href']
                    
                    # Clean up the URL to get the directory path
                    if base_href.endswith('.html'):
                        base_url = base_href.rsplit('/', 1)[0] + '/'
                    elif not base_href.endswith('/'):
                        base_url = base_href + '/'
                    else:
                        base_url = base_href
                        
                    # Construct the correct URL for this specific district's advocacy guide
                    advocacy_url = base_url + "parent-advocacy-guide.html"
                    
                    # Update the District Sub-Navigation Menu (Avoid duplicates)
                    existing_nav = subnav.find('a', href=advocacy_url)
                    if not existing_nav:
                        nav_link = soup.new_tag('a', href=advocacy_url)
                        nav_link.string = "🛡️ Advocacy"
                        subnav.append(nav_link)

                        # Save the updated HTML back to the file
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(str(soup))
                        
                        print(f"✓ Added Advocacy link to: {file_path}")

# Run the script targeting the 'districts' folder
if __name__ == "__main__":
    print("Starting bulk update of all silo navigation bars...")
    update_all_silo_navs('districts')
    print("Finished updating all pages!")