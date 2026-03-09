import os
import glob
import re
from bs4 import BeautifulSoup

def format_spanish_iep_pages():
    """
    Reads the core content of the existing Spanish IEP pages and wraps 
    them in the polished HTML template structure of the English IEP pages.
    """
    print("Starting Spanish IEP formatting process...")
    
    # Target all Spanish IEP files in the es/distritos/ directory
    es_files = glob.glob('es/distritos/nyc-district-*/*.html')
    
    count = 0
    for es_filepath in es_files:
        # Standardize slashes
        es_filepath = es_filepath.replace('\\', '/')
        
        # Extract the district slug from the path (e.g., "nyc-district-01-lower-east-side")
        path_parts = es_filepath.split('/')
        if len(path_parts) < 3:
            continue
            
        district_slug = path_parts[-2]
        
        # Extract district number to help find the english file if slug differs slightly
        match = re.search(r'nyc-district-(\d+)', district_slug)
        if not match:
            continue
        dist_num = match.group(1)
        
        # 1. Find the corresponding English 'what-is-an-iep.html' to use as a template
        en_pattern = f'districts/nyc-district-{dist_num}*/what-is-an-iep.html'
        en_files = glob.glob(en_pattern)
        
        if not en_files:
            print(f"⚠️ Warning: Could not find English template for {district_slug}. Skipping.")
            continue
            
        en_template_path = en_files[0]
        
        # 2. Extract the raw Spanish content from the existing Spanish file
        with open(es_filepath, 'r', encoding='utf-8') as f:
            es_raw = f.read()
            
        es_soup = BeautifulSoup(es_raw, 'html.parser')
        
        # Try to find the main content block. Usually it's in a <div class="content"> or <main>
        # If it's just raw HTML output from markdown, we'll grab the whole body
        es_content_container = es_soup.find('div', class_='content')
        if es_content_container:
            es_core_content = str(es_content_container)
        else:
             es_core_content = str(es_soup.body) if es_soup.body else es_raw
             
        # Optional: remove header/footer if they were appended poorly in the old Spanish generation
        es_core_content = re.sub(r'<header>.*?</header>', '', es_core_content, flags=re.IGNORECASE | re.DOTALL)
        es_core_content = re.sub(r'<footer>.*?</footer>', '', es_core_content, flags=re.IGNORECASE | re.DOTALL)

        # 3. Read the beautifully formatted English Template
        with open(en_template_path, 'r', encoding='utf-8') as f:
            en_template = f.read()
            
        # 4. Perform the Injection and Translation of metadata
        
        # A) Swap the main content block
        # We look for the main content div in the English file and replace its contents
        # This regex looks for <div class="content">...</div> and replaces the inside
        content_pattern = re.compile(r'(<div class="content">).*?(</div>)', re.DOTALL)
        
        # If we successfully captured the Spanish content, inject it
        if '<h1' in es_core_content or '<h2' in es_core_content:
             # Ensure the div tag is preserved
             injection = f'\\1\n{es_core_content}\n\\2'
             new_html = content_pattern.sub(injection, en_template)
        else:
            print(f"⚠️ Warning: No valid content found in Spanish file for {district_slug}. Skipping.")
            continue

        # B) Update the SEO Title tag
        title_pattern = re.compile(r'<title>.*?</title>', re.IGNORECASE)
        new_title = f"<title>¿Qué es un IEP? Guía para Padres en el Distrito {dist_num} | NY Special Ed</title>"
        new_html = title_pattern.sub(new_title, new_html)
        
        # C) Update the Meta Description
        desc_pattern = re.compile(r'<meta\s+name="description"\s+content="[^"]*">', re.IGNORECASE)
        new_desc = f'<meta name="description" content="Guía completa sobre el Programa de Educación Individualizada (IEP) en el Distrito Escolar {dist_num} de Nueva York para familias hispanohablantes.">'
        new_html = desc_pattern.sub(new_desc, new_html)
        
        # D) Update the HTML Lang attribute
        lang_pattern = re.compile(r'<html\s+lang="en">', re.IGNORECASE)
        new_html = lang_pattern.sub('<html lang="es">', new_html)
        
        # E) Fix canonical link to point to the Spanish URL
        canonical_pattern = re.compile(r'<link\s+rel="canonical"\s+href="[^"]*">', re.IGNORECASE)
        new_canonical = f'<link rel="canonical" href="https://www.newyorkspecialed.net/{es_filepath}">'
        new_html = canonical_pattern.sub(new_canonical, new_html)

        # 5. Save the newly formatted Spanish file back to its location
        with open(es_filepath, 'w', encoding='utf-8') as f:
            f.write(new_html)
            
        print(f"✅ Formatted: {es_filepath}")
        count += 1

    print(f"\n🎉 Done! Successfully formatted {count} Spanish IEP pages using the English layout template.")

if __name__ == '__main__':
    format_spanish_iep_pages()