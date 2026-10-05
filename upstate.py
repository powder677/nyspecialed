#!/usr/bin/env python3
"""
update_site.py  -  newyorkspecialed.net site-wide updater

What it does (every .html file under ROOT):
  1. Replaces the site header with one consistent header.
  2. Districts menu: opens on hover, keyboard focus AND click/tap.
  3. Mobile: removes the "District Intelligence" email pop-up (<=768px).
  4. Adds the "Advocacy You Can Wear" store banner to every page that is NOT
     an NYC page (NYC = any path segment starting with "nyc-").
  5. Repoints every "View Advocacy Shop" footer link to the Printify store.

Safe to re-run: all injected code lives between nyse:* marker comments and is
replaced, not duplicated.

Usage:
    python update_site.py /path/to/site            # dry run (changes nothing)
    python update_site.py /path/to/site --apply    # write changes + backups
    python update_site.py /path/to/site --apply --nyc-prefix nyc- --nyc-prefix manhattan-
"""
import argparse, re, shutil, sys, time
from pathlib import Path

STORE_URL = "https://newyorkspecialed.printify.me/"

DISTRICT_LINKS = [  # (label, href) - edit freely
    ("All Districts", "/districts/"),
    ("NYC District 2 (Manhattan)", "/districts/nyc-district-02-upper-east-side/"),
    ("NYC District 15 (Brooklyn)", "/districts/nyc-district-15-park-slope/"),
    ("NYC District 30 (Queens)", "/districts/nyc-district-30-astoria/"),
    ("NYC District 31 (Staten Island)", "/districts/nyc-district-31-staten-island/"),
    ("NYC District 75", "/districts/nyc-district-75/"),
    ("Buffalo City Schools", "/districts/buffalo-city-sd/"),
]

BANNER_TEXT = {
    "en": ("Advocacy You Can Wear", "Shirts, totes and mugs for parents who show up prepared.", "Visit the Store"),
    "es": ("Defensa que puedes vestir", "Camisetas, bolsas y tazas para padres que se preparan.", "Visitar la tienda"),
}

SKIP_DIRS = {".git", "node_modules", ".nyse_backup", "_site", "venv", ".venv"}

# ---------------------------------------------------------------- templates
CSS = """
.nyse-header{position:sticky;top:0;z-index:1000;background:#fff;border-bottom:1px solid #e2e8f0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.nyse-header *{box-sizing:border-box}
.nyse-inner{max-width:1100px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between;min-height:60px}
.nyse-logo{font-weight:800;font-size:1.15rem;color:#1a365d;text-decoration:none}
.nyse-logo span{color:#2b6cb0}
.nyse-nav ul{list-style:none;margin:0;padding:0;display:flex;gap:4px;align-items:center}
.nyse-nav li{position:relative;margin:0;padding:0}
.nyse-nav a{display:block;padding:20px 14px;color:#2d3748;text-decoration:none;font-size:.95rem;font-weight:500}
.nyse-nav a:hover,.nyse-nav a:focus-visible{color:#2b6cb0}
.nyse-nav .nyse-shop{color:#fff;background:#2b6cb0;border-radius:6px;padding:8px 14px;margin-left:6px}
.nyse-nav .nyse-shop:hover{color:#fff;background:#1a365d}
.nyse-nav .nyse-sub{display:none;position:absolute;top:100%;left:0;min-width:260px;background:#fff;border:1px solid #e2e8f0;border-radius:0 0 8px 8px;box-shadow:0 8px 20px rgba(0,0,0,.12);flex-direction:column;gap:0;padding:6px 0}
.nyse-nav .nyse-sub a{padding:10px 18px;white-space:nowrap}
.nyse-nav .nyse-sub a:hover{background:#f4f8fc}
.nyse-toggle{display:none;background:none;border:0;font-size:1.6rem;line-height:1;padding:8px;cursor:pointer;color:#1a365d}
@media (hover:hover) and (min-width:769px){
  .nyse-has-sub:hover>.nyse-sub{display:flex}
}
.nyse-has-sub:focus-within>.nyse-sub,.nyse-has-sub.nyse-open>.nyse-sub{display:flex}
@media (max-width:768px){
  .nyse-toggle{display:block}
  .nyse-nav{display:none;position:absolute;top:100%;left:0;right:0;background:#fff;border-bottom:1px solid #e2e8f0;box-shadow:0 8px 20px rgba(0,0,0,.1)}
  .nyse-nav.nyse-open{display:block}
  .nyse-nav ul{flex-direction:column;align-items:stretch;gap:0}
  .nyse-nav a{padding:14px 20px;border-top:1px solid #f1f5f9}
  .nyse-nav .nyse-sub{position:static;box-shadow:none;border:0;border-radius:0;background:#f8fafc;min-width:0}
  .nyse-nav .nyse-sub a{padding-left:36px;white-space:normal}
  .nyse-nav .nyse-shop{margin:10px 20px;text-align:center}
}
.nyse-banner{background:#1a365d;color:#fff;text-align:center;padding:10px 16px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;font-size:.92rem}
.nyse-banner strong{letter-spacing:.02em}
.nyse-banner a{color:#fff;font-weight:700;text-decoration:underline;margin-left:8px;white-space:nowrap}
"""

JS = r"""
(function(){
  /* ---- header: menu + Districts dropdown ---- */
  var toggle=document.querySelector('.nyse-toggle'), nav=document.getElementById('nyse-nav');
  if(toggle&&nav){toggle.addEventListener('click',function(){
    var o=nav.classList.toggle('nyse-open');toggle.setAttribute('aria-expanded',o);});}
  var sub=document.querySelector('.nyse-has-sub'), link=sub&&sub.querySelector('.nyse-sub-toggle');
  function touchMode(){return window.matchMedia('(max-width:768px), (hover:none)').matches;}
  if(link){
    link.addEventListener('click',function(e){
      if(touchMode()){e.preventDefault();var o=sub.classList.toggle('nyse-open');link.setAttribute('aria-expanded',o);}
    });
    document.addEventListener('keydown',function(e){if(e.key==='Escape'){sub.classList.remove('nyse-open');link.setAttribute('aria-expanded','false');}});
    document.addEventListener('click',function(e){if(!sub.contains(e.target)){sub.classList.remove('nyse-open');}});
  }

  /* ---- mobile: remove email-capture pop-up ---- */
  var mq=window.matchMedia('(max-width:768px)');
  var LABELS=['District Intelligence',"You're on the list"];
  function unlock(){
    [document.body,document.documentElement].forEach(function(el){
      el.style.setProperty('overflow','auto','important');
      el.className=(el.className||'').replace(/\b[\w-]*(modal|no-?scroll|lock)[\w-]*\b/gi,'').trim();
    });
  }
  function kill(){
    if(!mq.matches||!document.body)return;
    var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),n,hit=false;
    while((n=w.nextNode())){
      if(!LABELS.some(function(t){return n.nodeValue.indexOf(t)>-1;}))continue;
      var el=n.parentElement,target=null;
      while(el&&el!==document.body){
        var cs=getComputedStyle(el);
        if(cs.position==='fixed'){target=el;}
        else if(!target&&/modal|popup|pop-up|overlay|capture|subscribe/i.test((el.id||'')+' '+(el.className||''))){target=el;}
        el=el.parentElement;
      }
      if(target){target.style.setProperty('display','none','important');hit=true;}
    }
    if(hit)unlock();
  }
  kill();
  document.addEventListener('DOMContentLoaded',kill);
  [500,1500,3000,6000,12000].forEach(function(t){setTimeout(kill,t);});
  if(window.MutationObserver){
    var mo=new MutationObserver(function(){kill();});
    mo.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['class','style']});
    setTimeout(function(){mo.disconnect();},30000);
  }
})();
"""


def header_html(lang):
    es = lang == "es"
    lang_href, lang_label = ("/", "🇺🇸 English") if es else ("/guides/es/index.html", "🇪🇸 En Español")
    subs = "\n".join(f'<li><a href="{h}">{l}</a></li>' for l, h in DISTRICT_LINKS)
    return f"""<!-- nyse:header:start -->
<div class="nyse-header" role="banner">
  <div class="nyse-inner">
    <a class="nyse-logo" href="/">NY SpecialEd<span>.net</span></a>
    <button class="nyse-toggle" type="button" aria-label="Menu" aria-controls="nyse-nav" aria-expanded="false">&#9776;</button>
    <div class="nyse-nav" id="nyse-nav" role="navigation" aria-label="Main">
      <ul>
        <li class="nyse-has-sub">
          <a class="nyse-sub-toggle" href="/districts/" aria-haspopup="true" aria-expanded="false">Districts &#9662;</a>
          <ul class="nyse-sub">
{subs}
          </ul>
        </li>
        <li><a href="/guides/">Parent Guides</a></li>
        <li><a href="{lang_href}">{lang_label}</a></li>
        <li><a href="/resources/">Resources</a></li>
        <li><a class="nyse-shop" href="{STORE_URL}" target="_blank" rel="noopener sponsored">Shop</a></li>
      </ul>
    </div>
  </div>
</div>
<!-- nyse:header:end -->"""


def banner_html(lang):
    tag, blurb, cta = BANNER_TEXT[lang]
    return f"""<!-- nyse:banner:start -->
<div class="nyse-banner"><strong>{tag}</strong> &mdash; {blurb}<a href="{STORE_URL}" target="_blank" rel="noopener sponsored">{cta} &rarr;</a></div>
<!-- nyse:banner:end -->"""


# ---------------------------------------------------------------- helpers
def block(name):
    return re.compile(rf"<!-- nyse:{name}:start -->.*?<!-- nyse:{name}:end -->\s*", re.S)


def is_nyc(rel, prefixes):
    return any(seg.lower().startswith(tuple(prefixes)) for seg in rel.parts)


def lang_of(rel):
    return "es" if "es" in rel.parts[:-1] else "en"


def process(html, rel, prefixes, log):
    orig = html
    lang = lang_of(rel)

    # --- CSS + JS (replace or insert)
    css = f"<!-- nyse:css:start -->\n<style>{CSS}</style>\n<!-- nyse:css:end -->\n"
    js = f"<!-- nyse:js:start -->\n<script>{JS}</script>\n<!-- nyse:js:end -->\n"
    html = block("css").sub("", html)
    html = block("js").sub("", html)
    if re.search(r"</head>", html, re.I):
        html = re.sub(r"</head>", lambda m: css + m.group(0), html, count=1, flags=re.I)
    else:
        log.append("no </head> - CSS prepended"); html = css + html
    if re.search(r"</body>", html, re.I):
        html = re.sub(r"</body>", lambda m: js + m.group(0), html, count=1, flags=re.I)
    else:
        log.append("no </body> - JS appended"); html += js

    # --- header
    html = block("banner").sub("", html)  # remove first so re-runs are byte-stable
    hdr = header_html(lang)
    if block("header").search(html):
        html = block("header").sub(lambda m: hdr + "\n", html, count=1)
    else:
        done = False
        for m in re.finditer(r"<header\b.*?</header>", html, re.S | re.I):
            if re.search(r"districts|<nav", m.group(0), re.I):  # site header, not a page hero
                html = html[:m.start()] + hdr + html[m.end():]; done = True; break
        if not done:
            m = re.search(r"<nav\b.*?</nav>", html, re.S | re.I)
            if m:
                html = html[:m.start()] + hdr + html[m.end():]; done = True; log.append("replaced <nav> (no <header> found)")
        if not done:
            html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + hdr, html, count=1, flags=re.I)
            log.append("no existing header found - inserted after <body>; check for a leftover old menu")

    # --- banner (non-NYC only)
    if is_nyc(rel, prefixes):
        log.append("NYC page: no banner")
    else:
        html = html.replace("<!-- nyse:header:end -->", "<!-- nyse:header:end -->\n" + banner_html(lang), 1)

    # --- footer "View Advocacy Shop" link
    def fix(m):
        attrs = re.sub(r'\s(href|target|rel)="[^"]*"', "", m.group(1))
        return f'<a{attrs} href="{STORE_URL}" target="_blank" rel="noopener sponsored">{m.group(2)}</a>'
    html, n = re.subn(r"<a\b([^>]*)>(\s*(?:View\s+)?Advocacy Shop[^<]*)</a>", fix, html, flags=re.I)
    if n:
        log.append(f"footer shop link fixed x{n}")

    return html, html != orig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--apply", action="store_true", help="write changes (default is dry run)")
    ap.add_argument("--nyc-prefix", action="append", default=None,
                    help='path-segment prefix that marks an NYC page (default: "nyc-")')
    a = ap.parse_args()
    root = Path(a.root).resolve()
    prefixes = a.nyc_prefix or ["nyc-"]
    backup = root / ".nyse_backup" / time.strftime("%Y%m%d-%H%M%S")

    changed = banners = 0
    for f in sorted(root.rglob("*.html")):
        rel = f.relative_to(root)
        if SKIP_DIRS & set(rel.parts):
            continue
        text = f.read_text(encoding="utf-8")
        log = []
        new, did = process(text, rel, prefixes, log)
        has_banner = "nyse:banner:start" in new
        banners += has_banner
        print(f"{'CHANGE' if did else 'same  '}  {rel}  {'[banner]' if has_banner else ''}  {'; '.join(log)}")
        if did:
            changed += 1
            if a.apply:
                (backup / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, backup / rel)
                f.write_text(new, encoding="utf-8")
    mode = "APPLIED" if a.apply else "DRY RUN (nothing written; add --apply)"
    print(f"\n{mode}: {changed} files changed, {banners} pages with store banner.")
    if a.apply and changed:
        print(f"Originals backed up in {backup}")


if __name__ == "__main__":
    sys.exit(main())