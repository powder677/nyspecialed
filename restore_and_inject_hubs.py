import os
import glob
import re

def restore_and_inject_hubs():
    """
    Completely rebuilds the <div class="hub-grid"> block for all NYC 
    districts, restoring any lost cards and perfectly injecting the Spanish card.
    """
    files = glob.glob('districts/nyc-district-*/index.html')
    
    count = 0
    for filepath in files:
        # Extract the slug (e.g., "nyc-district-01-lower-east-side")
        slug = filepath.replace('\\', '/').split('/')[-2]
        
        # Extract district number (e.g., "01")
        match = re.search(r'nyc-district-(\d+)', slug)
        if not match:
            continue
        dist_num = match.group(1)
        
        # 1. Find the Spanish link dynamically
        es_pattern = f'es/distritos/nyc-district-{dist_num}-*/*.html'
        es_files = glob.glob(es_pattern)
        
        spanish_card_html = ""
        if es_files:
            es_file_path = es_files[0].replace('\\', '/')
            full_url = f"https://www.newyorkspecialed.net/{es_file_path}"
            spanish_card_html = f"""<a class="hub-card" href="{full_url}">
<h3 style="color: #0056b3; margin-top: 0;">🌐 ¿Qué Es un IEP? (Español)</h3>
<p>Guía completa sobre el IEP en el Distrito {dist_num} para familias hispanohablantes.</p>
</a>\n"""

        # 2. Build the 100% pristine, perfect grid block
        pristine_grid = f"""<div class="hub-grid">
<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/leadership-directory.html">
<h3 style="color: #0056b3; margin-top: 0;">📞 Contacts</h3>
<p>Phone numbers &amp; emails for CSE Chairperson.</p>
</a>
<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/cse-meeting-guide.html">
<h3 style="color: #0056b3; margin-top: 0;">🤝 CSE Guide</h3>
<p>What to expect at your Annual Review.</p>
</a>
<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/evaluation-process.html">
<h3 style="color: #0056b3; margin-top: 0;">📝 Evaluations</h3>
<p>How to trigger the 60-day timeline.</p>
</a>
<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/discipline-rights.html">
<h3 style="color: #0056b3; margin-top: 0;">⚖️ Discipline</h3>
<p>Suspensions and MDR rights.</p>
</a>
<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/partners.html">
<h3 style="color: #0056b3; margin-top: 0;">🤲 Partners</h3>
<p>Local advocates, legal aid, and support organizations.</p>
</a>
<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/special-ed-updates.html">
<h3 style="color: #0056b3; margin-top: 0;">📰 Updates</h3>
<p>Latest news and policy changes affecting your district.</p>
</a>
<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/parent-advocacy-guide.html">
<h3 style="color: #0056b3; margin-top: 0;">🛡️ Advocacy</h3>
<p>Strategies for navigating the CSE process and asserting your rights.</p>
</a>
{spanish_card_html}<a class="hub-card" href="https://www.newyorkspecialed.net/districts/{slug}/what-is-an-iep.html">
<h3 style="color: #0056b3; margin-top: 0;">📋 What Is an IEP?</h3>
<p>Plain-language guide to the IEP document, eligibility, and services in this district.</p>
</a>
</div>"""

        # 3. Read the broken file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 4. Safely swap out the entire corrupted grid for the pristine one
        # This matches <div class="hub-grid"> and stops at the very first </div>
        pattern = re.compile(r'<div class="hub-grid">.*?</div>', re.DOTALL)
        new_content = pattern.sub(pristine_grid, content)
        
        # Save it
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Restored & Injected: {slug}")
            count += 1
            
    print(f"\n🎉 Done! Fully restored {count} NYC district hub grids.")

if __name__ == '__main__':
    restore_and_inject_hubs()