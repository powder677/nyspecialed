import os
from bs4 import BeautifulSoup

def process_all_district_indexes(base_dir):
    # Walk through all folders and files in the base directory
    for root, dirs, files in os.walk(base_dir):
        if 'index.html' in files:
            file_path = os.path.join(root, 'index.html')
            
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            # Look for the specific layout components of a district hub
            hub_grid = soup.find('div', class_='hub-grid')
            subnav = soup.find('nav', class_='district-subnav')

            # Only process if it's a district hub page (contains both grid and subnav)
            if hub_grid and subnav:
                
                # Dynamically determine this specific district's URL base
                # We do this by grabbing an existing link from the subnav and extracting the base path
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
                
                # 1. Update the Card Grid (Avoid duplicates)
                existing_card = hub_grid.find('a', href=advocacy_url)
                if not existing_card:
                    new_card = soup.new_tag('a', href=advocacy_url, attrs={"class": "hub-card"})
                    
                    h3 = soup.new_tag('h3', style="color: #0056b3; margin-top: 0;")
                    h3.string = "🛡️ Advocacy"
                    
                    p = soup.new_tag('p')
                    p.string = "Strategies for navigating the CSE process and asserting your rights."
                    
                    new_card.append(h3)
                    new_card.append(p)
                    hub_grid.append(new_card)
                    
                # 2. Update the District Sub-Navigation Menu (Avoid duplicates)
                existing_nav = subnav.find('a', href=advocacy_url)
                if not existing_nav:
                    nav_link = soup.new_tag('a', href=advocacy_url)
                    nav_link.string = "🛡️ Advocacy"
                    subnav.append(nav_link)

                # Save the updated HTML back to the file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(str(soup))
                
                print(f"✓ Successfully updated: {file_path}")

# Run the script targeting the 'districts' folder
if __name__ == "__main__":
    print("Starting bulk update of district index pages...")
    process_all_district_indexes('districts')
    print("Finished updating all pages!")