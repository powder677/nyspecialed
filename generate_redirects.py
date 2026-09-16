#!/usr/bin/env python3
import csv
import os
import argparse

def generate_redirects(host_type="netlify", dry_run=True):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    dup_csv = os.path.join(root_dir, 'redirect_pairs_duplicates.csv')
    dead_csv = os.path.join(root_dir, 'redirect_pairs_dead_es.csv')
    
    rules = []
    
    # 1. Process format duplicates (no trailing slash / index.html -> canonical with slash)
    if os.path.exists(dup_csv):
        with open(dup_csv, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # skip header if present
            for row in reader:
                if len(row) >= 2:
                    old_url, new_url = row[0].strip(), row[1].strip()
                    # extract pathname
                    old_path = old_url.replace('https://www.newyorkspecialed.net', '').replace('http://www.newyorkspecialed.net', '')
                    new_path = new_url.replace('https://www.newyorkspecialed.net', '').replace('http://www.newyorkspecialed.net', '')
                    if old_path and new_path and old_path != new_path:
                        rules.append((old_path, new_path, 301))
                        
    # 2. Process dead /es/distritos/ URLs -> redirect target
    target_es = '/guides/es/index.html' # Aligned with Task 2 Option A
    if os.path.exists(dead_csv):
        with open(dead_csv, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 1:
                    old_url = row[0].strip()
                    old_path = old_url.replace('https://www.newyorkspecialed.net', '').replace('http://www.newyorkspecialed.net', '')
                    if old_path:
                        rules.append((old_path, target_es, 301))
                        
    print(f"Generated {len(rules)} total redirect rules.")
    
    if host_type in ['netlify', 'cloudflare']:
        output_file = os.path.join(root_dir, '_redirects')
        content = "\n".join([f"{src} {dst} {code}" for src, dst, code in rules]) + "\n"
    elif host_type == 'vercel':
        output_file = os.path.join(root_dir, 'vercel.json')
        import json
        redirect_list = [{"source": src, "destination": dst, "permanent": True} for src, dst, code in rules]
        content = json.dumps({"redirects": redirect_list}, indent=2)
    else:
        print("Unknown host type.")
        return
        
    if dry_run:
        print(f"\n[DRY RUN] Would write to {output_file}:")
        print(content[:500] + "\n... [truncated for dry-run preview] ...")
    else:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully wrote redirect configuration to {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['netlify', 'cloudflare', 'vercel'], default='netlify')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    generate_redirects(host_type=args.host, dry_run=args.dry_run)