#!/usr/bin/env python3
"""
Rewrites <loc> entries in sitemap.xml so they match each page's canonical URL,
using the "Non-canonical page in sitemap" export (columns: URL, Canonical URL).

Dry run by default. Add --apply to write.

  python fix_sitemap_canonicals.py --csv "export.csv" --sitemap sitemap.xml
  python fix_sitemap_canonicals.py --csv "export.csv" --sitemap sitemap.xml --apply
"""
import argparse
import csv
import re
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--sitemap", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with open(args.csv, encoding="utf-8-sig", newline="") as fh:
        mapping = {
            r["URL"].strip(): r["Canonical URL"].strip()
            for r in csv.DictReader(fh)
            if r.get("URL") and r.get("Canonical URL")
        }

    with open(args.sitemap, encoding="utf-8", newline="") as fh:
        xml = fh.read()

    count = 0

    def sub(m):
        nonlocal count
        url = m.group(2).strip()
        new = mapping.get(url)
        if new and new != url:
            count += 1
            return f"{m.group(1)}{new}{m.group(3)}"
        return m.group(0)

    new_xml = re.sub(r"(<loc>\s*)(.*?)(\s*</loc>)", sub, xml, flags=re.S)

    print(f"{count} of {len(mapping)} URLs {'updated' if args.apply else 'would be updated'}")
    if count < len(mapping):
        print("Some URLs in the CSV were not found in this sitemap (already fixed, or a different file).")
    if args.apply and count:
        with open(args.sitemap, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_xml)
    elif not args.apply:
        print("Re-run with --apply to write the changes.")


if __name__ == "__main__":
    main()