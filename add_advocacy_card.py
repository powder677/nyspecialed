import os
from bs4 import BeautifulSoup

def add_advocacy_to_index(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # 1. Update the Card Grid
    hub_grid = soup.find('div', class_='hub-grid')
    if hub_grid:
        # Create the new <a> wrapper
        new_card = soup.new_tag('a', 
                                href="https://www.newyorkspecialed.net/districts/central-islip-ufsd/parent-advocacy-guide.html", 
                                attrs={"class": "hub-card"})
        
        # Create the <h3> heading with inline styles
        h3 = soup.new_tag('h3', style="color: #0056b3; margin-top: 0;")
        h3.string = "🛡️ Advocacy"
        
        # Create the <p> description
        p = soup.new_tag('p')
        p.string = "Strategies for navigating the CSE process and asserting your rights."
        
        # Assemble the card and append to grid
        new_card.append(h3)
        new_card.append(p)
        hub_grid.append(new_card)
        print("✓ Successfully added 'Advocacy' card to the hub-grid.")

    # 2. Update the District Sub-Navigation Menu
    subnav = soup.find('nav', class_='district-subnav')
    if subnav:
        # Create the navigation link
        nav_link = soup.new_tag('a', href="https://www.newyorkspecialed.net/districts/central-islip-ufsd/parent-advocacy-guide.html")
        nav_link.string = "🛡️ Advocacy"
        
        # Append to the subnav
        subnav.append(nav_link)
        print("✓ Successfully added 'Advocacy' link to the district-subnav.")

    # Save the updated HTML
    with open(file_path, 'w', encoding='utf-8') as file:
        # Using str() preserves your existing formatting better than prettify()
        file.write(str(soup))

# Run the function on your index file
add_advocacy_to_index('index.html')