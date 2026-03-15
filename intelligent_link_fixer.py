import os
import re

# =========================================================
# CONFIGURATION & MAPPING RULES
# =========================================================

# The root directory of your website (use '.' if running from the root)
PROJECT_ROOT = "."

KNOWN_FIXES = {
    # 1. Unresolved Template Placeholders
    "EVALUATION_PROCESS_PAGE_URL": "evaluation-process.html",
    "CSE_MEETING_GUIDE_PAGE_URL": "cse-meeting-guide.html",
    "ADVOCACY_PAGE_URL": "parent-advocacy-guide.html",
    "GLOSSARY_PAGE_URL": "/guides/index.html", 
    "/districts/${d.slug}/index.html": "/districts/index.html", # Missed literal template string

    # 2. Old CamelCase Links and Directories
    "CSEMeetingGuide.html": "cse-meeting-guide.html",
    "EvaluationProcess.html": "evaluation-process.html",
    "ServicesAndPlacement.html": "cse-meeting-guide.html",
    "CSEMeetingGuide/": "cse-meeting-guide.html",
    "EvaluationProcess/": "evaluation-process.html",
    "ServicesAndPlacement/": "cse-meeting-guide.html",
    "YourRights/": "parent-advocacy-guide.html",

    # 3. Broken Hub/Root Links improperly nested
    "/districts/Placement-Options": "/guides/carter-cases-private-placement/index.html",
    "/districts/Parent-Rights-in-Special-Education": "/guides/parent-advocacy-guide/index.html",
    "/districts/Parent-Rights": "/guides/parent-advocacy-guide/index.html",
    "/districts/Advocacy-Tips": "/guides/parent-advocacy-guide/index.html",
    "/districts/Resolving-Disputes": "/guides/dispute-resolution-ny/index.html",
    "/districts/IEP-Process": "/guides/cse-meeting-guide/index.html",
    "/districts/Community-Resources": "/resources/index.html",
    "/districts/Glossary": "/guides/index.html",
    "/districts/504": "/guides/index.html",
    "/districts/Special-Education-Services": "/guides/index.html",

    # 4. Missing Guide Folder Hubs
    "/guides/iep-guide/": "/guides/index.html",
    "/guides/special-ed-law/": "/guides/index.html",
    "/guides/placement-options/": "/guides/carter-cases-private-placement/index.html",
    "/guides/iep-development/": "/guides/index.html",
    "/guides/services/": "/guides/index.html",
    "/guides/504-plans/": "/guides/index.html",
    "/guides/iee/": "/guides/evaluation-request-ny/index.html",
    "/guides/parent-rights/": "/guides/parent-advocacy-guide/index.html",
    "/guides/iep-services/": "/guides/index.html",
    
    # 5. Broken Direct Root Links
    "/disputes": "/guides/dispute-resolution-ny/index.html",
    "/dispute-resolution": "/guides/dispute-resolution-ny/index.html",
    "/accommodations": "/guides/cse-meeting-guide/index.html",
    "/cse-meeting-guide": "/guides/cse-meeting-guide/index.html",
    "/cse-meeting": "/guides/cse-meeting-guide/index.html",
    "/advocacy": "/guides/parent-advocacy-guide/index.html",

    # 6. Orphaned CSS fixes
    "/styles/partners.css": "/styles/global.css",
}

LINK_PATTERN = re.compile(r'href=(["\'])(.*?)\1')

total_files_scanned = 0
total_links_checked = 0
links_fixed = []
links_unfixable = []

def does_local_file_exist(current_file_path, href):
    if href.startswith(('http', 'https', 'mailto:', 'tel:', '#', 'javascript:')):
        return True 

    clean_href = href.split('?')[0].split('#')[0]
    if not clean_href:
        return True

    if clean_href.startswith('/'):
        target_path = os.path.join(PROJECT_ROOT, clean_href.lstrip('/'))
    else:
        current_dir = os.path.dirname(current_file_path)
        target_path = os.path.join(current_dir, clean_href)
    
    if os.path.isdir(target_path):
        target_path = os.path.join(target_path, 'index.html')

    return os.path.exists(target_path)

def attempt_to_fix_link(broken_href):
    if broken_href in KNOWN_FIXES:
        return KNOWN_FIXES[broken_href]
    
    clean_href = broken_href.split('?')[0].split('#')[0]
    for bad_pattern, fix in KNOWN_FIXES.items():
        if bad_pattern in clean_href:
            return fix

    # DYNAMIC LOGIC FIX: Turn trailing slash directories into .html files
    if not clean_href.endswith('.html') and not clean_href.endswith('.css'):
        stripped = clean_href.rstrip('/')
        if stripped and not stripped.endswith('.'): # Avoids formatting "../" into "...html"
            return stripped + '.html'

    return None

print("Starting intelligent link audit and fixing process V2...")

for root, dirs, files in os.walk(PROJECT_ROOT):
    for filename in files:
        if filename.endswith(".html"):
            total_files_scanned += 1
            file_path = os.path.join(root, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            def link_replacer(match):
                global total_links_checked
                quote_char = match.group(1)
                href = match.group(2)
                original_href = href
                
                if href.startswith(('http', 'mailto:', 'tel:', '#', 'javascript:')):
                    return match.group(0)
                
                total_links_checked += 1

                if not does_local_file_exist(file_path, href):
                    new_href = attempt_to_fix_link(href)
                    
                    if new_href:
                        if does_local_file_exist(file_path, new_href):
                            links_fixed.append(f"FIXED in {file_path}: [{original_href}] -> [{new_href}]")
                            return f'href={quote_char}{new_href}{quote_char}'
                        else:
                            links_unfixable.append(f"UNFIXABLE (Missing Target) in {file_path}: [{original_href}] -> [{new_href}]")
                    else:
                        links_unfixable.append(f"BROKEN (No known fix) in {file_path}: [{original_href}]")
                
                return match.group(0)

            new_content = LINK_PATTERN.sub(link_replacer, content)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

report_content = f"""
==================================================
        INTELLIGENT LINK FIXER REPORT V2
==================================================
Files Scanned: {total_files_scanned}
Total Internal Links Checked: {total_links_checked}
Successfully Fixed Links: {len(links_fixed)}
Broken Links Remaining: {len(links_unfixable)}
==================================================

=== SUCCESSFULLY FIXED ===
""" + "\n".join(links_fixed) + """

=== UNFIXABLE / STILL BROKEN ===
""" + "\n".join(links_unfixable)

print(f"\nAudit complete! Scanned {total_files_scanned} files.")
print(f"Fixed {len(links_fixed)} links.")
print(f"Found {len(links_unfixable)} broken links that require manual attention.")
print("Detailed results saved to 'link_audit_report.txt'.")

with open("link_audit_report.txt", "w", encoding='utf-8') as f:
    f.write(report_content)