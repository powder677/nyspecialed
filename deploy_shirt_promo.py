"""
NYC page promo deploy — 3-in-1:
  1. Removes any lingering newsletter/email-capture popup markup + its script tag.
  2. Adds an "obnoxious" full-width banner under the nav bar.
  3. Adds a sticky floating tab on the right edge (all screen sizes).
  4. Adds/updates the quieter banner just above the footer (from before).

Run from the root of your site repo:
  python deploy_shirt_promo.py --dry-run     # preview, changes nothing
  python deploy_shirt_promo.py               # apply
  python deploy_shirt_promo.py --remove      # strip all 3 banners (popup stays removed)

Safe to re-run — every block is wrapped in marker comments, so re-running
replaces old blocks instead of stacking duplicates.
"""

import argparse
import glob
import re

# ---------------------------------------------------------------- CONFIG ----
SHIRT_URL   = "https://newyorkspecialed.printify.me/product/32499964"
SHIRT_NAME  = "Mr Mayor!"
SHIRT_BLURB = "Wear your advocacy. Designed for NYC parents who show up."
SHIRT_PRICE = ""                            # e.g. "$24" (leave "" to hide)
SHIRT_IMAGE = "/images/mr-mayor-shirt.jpg"  # leave "" for text-only banners
BUTTON_TEXT = "Shop the Shirt"
TOP_BUTTON_TEXT = "GET THE SHIRT"
PAGE_GLOB   = "districts/nyc-district-*/**/*.html"
REMOVE_LEGACY_POPUP = True   # strip any lingering email-capture popup while we're in here
# ---------------------------------------------------------------------------

FOOTER_START, FOOTER_END = "<!-- shirt-promo:start -->", "<!-- shirt-promo:end -->"
TOP_START,    TOP_END    = "<!-- shirt-promo-top:start -->", "<!-- shirt-promo-top:end -->"
SIDE_START,   SIDE_END   = "<!-- shirt-promo-side:start -->", "<!-- shirt-promo-side:end -->"

FOOTER_RE = re.compile(re.escape(FOOTER_START) + r".*?" + re.escape(FOOTER_END) + r"\s*", re.S)
TOP_RE    = re.compile(re.escape(TOP_START)    + r".*?" + re.escape(TOP_END)    + r"\s*", re.S)
SIDE_RE   = re.compile(re.escape(SIDE_START)   + r".*?" + re.escape(SIDE_END)   + r"\s*", re.S)

# Matches the whole "Premium Newsletter Popup" block (comment header through its <script> tag)
POPUP_RE = re.compile(
    r"<!--\s*=+\s*\n\s*NY Special Ed.*?<script src=\"/scripts/newsletter-popup\.js\"[^>]*></script>\s*",
    re.S,
)


def build_footer_block():
    img = (
        f'<img src="{SHIRT_IMAGE}" alt="{SHIRT_NAME}" loading="lazy" '
        f'style="width:110px;height:110px;object-fit:cover;border-radius:4px;flex-shrink:0;">'
        if SHIRT_IMAGE else ""
    )
    price = f'<span style="color:#d4af37;font-weight:600;margin-left:8px;">{SHIRT_PRICE}</span>' if SHIRT_PRICE else ""
    return f"""{FOOTER_START}
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
{FOOTER_END}
"""


def build_top_block():
    return f"""{TOP_START}
<div id="shirt-top-banner" style="background:linear-gradient(90deg,#c8102e,#a80d24 50%,#c8102e);border-bottom:3px solid #d4af37;padding:12px 16px;">
  <style>
    @keyframes shirtPulse {{ 0%,100%{{transform:scale(1);}} 50%{{transform:scale(1.05);}} }}
    #shirt-top-banner .shirt-cta {{ animation:shirtPulse 1.4s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{ #shirt-top-banner .shirt-cta {{ animation:none; }} }}
  </style>
  <div style="max-width:1160px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;font-family:'DM Sans',sans-serif;position:relative;">
    <span style="font-size:22px;line-height:1;">🚨</span>
    <span style="color:#fff;font-weight:700;font-size:15px;letter-spacing:.02em;">NEW: THE "{SHIRT_NAME.upper()}" SHIRT IS HERE</span>
    <a href="{SHIRT_URL}" target="_blank" rel="noopener" class="shirt-cta" style="display:inline-block;background:#ffd700;color:#002868;text-decoration:none;font-weight:800;font-size:13px;letter-spacing:.03em;padding:8px 18px;border-radius:20px;">{TOP_BUTTON_TEXT} &rarr;</a>
    <button onclick="document.getElementById('shirt-top-banner').style.display='none'" aria-label="Dismiss" style="position:absolute;right:0;top:50%;transform:translateY(-50%);background:none;border:none;color:#fff;opacity:.7;font-size:16px;cursor:pointer;padding:4px 8px;">✕</button>
  </div>
</div>
{TOP_END}
"""


def build_side_block():
    img = (
        f'<img src="{SHIRT_IMAGE}" alt="{SHIRT_NAME}" loading="lazy" '
        f'style="width:64px;height:64px;object-fit:cover;border-radius:4px;margin-bottom:6px;">'
        if SHIRT_IMAGE else ""
    )
    return f"""{SIDE_START}
<div id="shirt-side-tab" style="position:fixed;right:14px;top:50%;transform:translateY(-50%);z-index:9500;font-family:'DM Sans',sans-serif;">
  <div style="position:relative;background:#002868;border:2px solid #d4af37;border-radius:10px;padding:16px 14px;width:120px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,.3);">
    <button onclick="document.getElementById('shirt-side-tab').style.display='none'" aria-label="Dismiss" style="position:absolute;top:2px;right:4px;background:none;border:none;color:rgba(255,255,255,.6);font-size:13px;cursor:pointer;">✕</button>
    {img}
    <div style="color:#d4af37;font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px;">New Merch</div>
    <div style="color:#f5f0e8;font-size:13px;font-weight:600;line-height:1.2;margin-bottom:8px;">{SHIRT_NAME}</div>
    <a href="{SHIRT_URL}" target="_blank" rel="noopener" style="display:block;background:#c8102e;color:#fff;text-decoration:none;font-weight:700;font-size:11px;padding:8px 6px;border-radius:4px;">SHOP NOW</a>
  </div>
</div>
{SIDE_END}
"""


def process(path, footer_block, top_block, side_block, remove):
    # Universal-newline read (CRLF/CR normalized to \n) so inserted blocks
    # (which use \n) don't leave the file with mixed line endings.
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    original = html

    if REMOVE_LEGACY_POPUP:
        html = POPUP_RE.sub("", html)

    html = FOOTER_RE.sub("", html)
    html = TOP_RE.sub("", html)
    html = SIDE_RE.sub("", html)

    if not remove:
        # Footer block: just above <footer class="site-footer...">, else just above </body>
        m = re.search(r'<footer\b[^>]*class="[^"]*site-footer', html) or re.search(r"</body>", html)
        if m:
            html = html[:m.start()] + footer_block + html[m.start():]

        # Top block: right after </header>
        m = re.search(r"</header>", html)
        if m:
            html = html[:m.end()] + "\n" + top_block + html[m.end():]

        # Side block: right after <body>, since it's position:fixed it doesn't matter where in the DOM
        m = re.search(r"<body[^>]*>", html)
        if m:
            html = html[:m.end()] + "\n" + side_block + html[m.end():]

    return html if html != original else False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(PAGE_GLOB, recursive=True))
    footer_block, top_block, side_block = build_footer_block(), build_top_block(), build_side_block()
    changed = skipped = 0

    for p in files:
        result = process(p, footer_block, top_block, side_block, args.remove)
        if result is False:
            skipped += 1
        else:
            changed += 1
            if not args.dry_run:
                with open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write(result)

    mode = "Would update" if args.dry_run else "Updated"
    print(f"Scanned {len(files)} files | {mode}: {changed} | Unchanged: {skipped}")


if __name__ == "__main__":
    main()