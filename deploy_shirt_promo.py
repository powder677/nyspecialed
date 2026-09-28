"""
Adds (or updates) a shirt promo banner on every NYC district page.

Run from the root of your site repo:
  python deploy_shirt_promo.py --dry-run     # preview, changes nothing
  python deploy_shirt_promo.py               # apply

Safe to re-run: the banner is wrapped in marker comments, so re-running
replaces the old banner instead of stacking a second one. To remove it
everywhere, run with --remove.
"""

import argparse
import glob
import re

# ---------------------------------------------------------------- CONFIG ----
SHIRT_URL   = "https://newyorkspecialed.printify.me/product/32499964"
SHIRT_NAME  = "Mr Mayor!"
SHIRT_BLURB = "Wear your advocacy. Designed for NYC parents who show up."
SHIRT_PRICE = ""                                                # e.g. "$24" (leave "" to hide)
SHIRT_IMAGE = "/images/mr-mayor-shirt.jpg"                      # update path/name once you commit the file
BUTTON_TEXT = "Shop the Shirt"
# Which pages get it (NYC district folders, every page inside them):
PAGE_GLOB   = "districts/nyc-district-*/**/*.html"
# ---------------------------------------------------------------------------

START = "<!-- shirt-promo:start -->"
END   = "<!-- shirt-promo:end -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\s*", re.S)


def build_block():
    img = (
        f'<img src="{SHIRT_IMAGE}" alt="{SHIRT_NAME}" loading="lazy" '
        f'style="width:110px;height:110px;object-fit:cover;border-radius:4px;flex-shrink:0;">'
        if SHIRT_IMAGE else ""
    )
    price = (
        f'<span style="color:#d4af37;font-weight:600;margin-left:8px;">{SHIRT_PRICE}</span>'
        if SHIRT_PRICE else ""
    )
    return f"""{START}
<section aria-label="Shirt promotion" style="max-width:860px;margin:40px auto;padding:0 16px;">
  <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;background:#002868;border-bottom:3px solid #d4af37;border-radius:6px;padding:22px 24px;font-family:'DM Sans',sans-serif;">
    {img}
    <div style="flex:1;min-width:220px;">
      <div style="font-size:10px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:#d4af37;margin-bottom:6px;">New Merch</div>
      <div style="font-family:'Cormorant Garamond',serif;font-size:26px;font-weight:500;color:#f5f0e8;line-height:1.15;">{SHIRT_NAME}{price}</div>
      <p style="margin:6px 0 0;font-size:14px;color:#cfd6e6;line-height:1.5;">{SHIRT_BLURB}</p>
    </div>
    <a href="{SHIRT_URL}" target="_blank" rel="noopener" style="background:#c8102e;color:#fff;text-decoration:none;font-weight:600;font-size:15px;padding:13px 22px;border-radius:4px;white-space:nowrap;">{BUTTON_TEXT} &rarr;</a>
  </div>
</section>
{END}
"""


def process(path, block, remove):
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        html = f.read()

    cleaned = BLOCK_RE.sub("", html)  # strip any previous banner
    if remove:
        new = cleaned
    else:
        # Place just above the footer; fall back to just above </body>
        m = re.search(r'<footer\b[^>]*class="[^"]*site-footer', cleaned) or re.search(r"</body>", cleaned)
        if not m:
            return None
        new = cleaned[:m.start()] + block + cleaned[m.start():]

    if new == html:
        return False
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    if not args.remove and "YOUR-STORE" in SHIRT_URL:
        print("Set SHIRT_URL / SHIRT_NAME at the top of the script first.")
        return

    files = sorted(glob.glob(PAGE_GLOB, recursive=True))
    block = build_block()
    changed = skipped = nofooter = 0

    for p in files:
        result = process(p, block, args.remove)
        if result is None:
            nofooter += 1
        elif result is False:
            skipped += 1
        else:
            changed += 1
            if not args.dry_run:
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(result)

    mode = "Would update" if args.dry_run else "Updated"
    print(f"Scanned {len(files)} files | {mode}: {changed} | Unchanged: {skipped} | No footer/body: {nofooter}")


if __name__ == "__main__":
    main()