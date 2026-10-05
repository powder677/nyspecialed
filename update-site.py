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
:root{--nyse-ink:#14110f;--nyse-gold:#d4a017;--nyse-gold-lt:#f3d36b}
.nyse-header{position:sticky;top:0;z-index:1000;background:#fff;border-bottom:1px solid #e2e8f0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.nyse-header *{box-sizing:border-box}
.nyse-inner{max-width:1100px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between;min-height:60px}
.nyse-logo{font-weight:800;font-size:1.15rem;color:var(--nyse-ink);text-decoration:none}
.nyse-logo span{color:var(--nyse-gold)}
.nyse-nav ul{list-style:none;margin:0;padding:0;display:flex;gap:4px;align-items:center}
.nyse-nav li{position:relative;margin:0;padding:0}
.nyse-nav a{display:block;padding:20px 14px;color:#2d3748;text-decoration:none;font-size:.95rem;font-weight:500}
.nyse-nav a:hover,.nyse-nav a:focus-visible{color:#8a6a00}
.nyse-nav .nyse-shop{color:var(--nyse-ink);font-weight:800;background:var(--nyse-gold);border-radius:6px;padding:8px 14px;margin-left:6px}
.nyse-nav .nyse-shop:hover{color:var(--nyse-gold);background:var(--nyse-ink)}
.nyse-nav .nyse-sub{display:none;position:absolute;top:100%;left:0;min-width:260px;background:#fff;border:1px solid #e2e8f0;border-radius:0 0 8px 8px;box-shadow:0 8px 20px rgba(0,0,0,.12);flex-direction:column;gap:0;padding:6px 0}
.nyse-nav .nyse-sub a{padding:10px 18px;white-space:nowrap}
.nyse-nav .nyse-sub a:hover{background:#faf5e4}
.nyse-toggle{display:none;background:none;border:0;font-size:1.6rem;line-height:1;padding:8px;cursor:pointer;color:var(--nyse-ink)}
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

/* ---- TOP BANNER ---- */
.nyse-banner{position:relative;overflow:hidden;background:linear-gradient(90deg,var(--nyse-gold),var(--nyse-gold-lt),var(--nyse-gold));color:var(--nyse-ink);text-align:center;padding:16px 16px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;border-bottom:4px solid var(--nyse-ink)}
.nyse-banner .nyse-b-tag{display:block;font-size:clamp(1.4rem,4.5vw,2.4rem);font-weight:900;letter-spacing:.06em;text-transform:uppercase;line-height:1.1}
.nyse-banner .nyse-b-sub{display:block;font-size:1rem;font-weight:600;margin:6px 0 10px}
.nyse-btn{display:inline-block;background:var(--nyse-ink);color:var(--nyse-gold-lt)!important;font-weight:800;text-transform:uppercase;letter-spacing:.05em;text-decoration:none!important;padding:12px 26px;border-radius:999px;border:2px solid var(--nyse-ink);animation:nysePulse 1.6s ease-in-out infinite}
.nyse-btn:hover{background:#fff;color:var(--nyse-ink)!important}
.nyse-banner:after{content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.55),transparent);animation:nyseShine 3.2s ease-in-out infinite}
@keyframes nysePulse{0%,100%{transform:scale(1);box-shadow:0 0 0 0 rgba(20,17,15,.5)}50%{transform:scale(1.07);box-shadow:0 0 0 10px rgba(20,17,15,0)}}
@keyframes nyseShine{0%{left:-60%}60%,100%{left:130%}}
/* ---- STICKY BOTTOM BAR ---- */
.nyse-bar{position:fixed;left:0;right:0;bottom:0;z-index:9999;display:flex;align-items:center;justify-content:center;gap:14px;flex-wrap:wrap;background:var(--nyse-ink);color:var(--nyse-gold-lt);border-top:4px solid var(--nyse-gold);padding:10px 48px 10px 16px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:.05em;font-size:.95rem;text-align:center}
.nyse-bar .nyse-btn{background:var(--nyse-gold);color:var(--nyse-ink)!important;border-color:var(--nyse-gold);padding:8px 20px}
.nyse-bar-x{position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:0;color:var(--nyse-gold-lt);font-size:1.6rem;line-height:1;cursor:pointer;padding:4px 8px}
body.nyse-bar-on{padding-bottom:72px}
/* ---- DESKTOP SIDE RAILS (only when the margins are empty) ---- */
.nyse-rail{display:none}
@media (min-width:1400px){
  .nyse-rail{display:flex;position:fixed;top:140px;width:130px;z-index:900;flex-direction:column;align-items:center;text-align:center;gap:10px;background:var(--nyse-ink);color:var(--nyse-gold-lt);border:3px solid var(--nyse-gold);border-radius:10px;padding:18px 10px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;text-decoration:none;box-shadow:0 6px 18px rgba(0,0,0,.25)}
  .nyse-rail-l{left:max(8px,calc((100vw - 1100px)/4 - 65px))}
  .nyse-rail-r{right:max(8px,calc((100vw - 1100px)/4 - 65px))}
  .nyse-rail .nyse-r-ico{font-size:2.6rem;line-height:1}
  .nyse-rail .nyse-r-tag{font-weight:900;text-transform:uppercase;letter-spacing:.05em;font-size:1rem;line-height:1.15}
  .nyse-rail .nyse-btn{background:var(--nyse-gold);color:var(--nyse-ink)!important;border-color:var(--nyse-gold);padding:8px 12px;font-size:.8rem}
  .nyse-rail:hover{transform:translateY(-4px)}
}
@media (prefers-reduced-motion:reduce){.nyse-btn,.nyse-banner:after{animation:none}}
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

  /* ---- bottom bar: dismiss for this session ---- */
  var bar=document.getElementById('nyse-bar');
  if(bar){
    var gone=false;try{gone=sessionStorage.getItem('nyseBar')==='1';}catch(e){}
    if(gone){bar.style.display='none';}else{document.body.classList.add('nyse-bar-on');}
    var x=bar.querySelector('.nyse-bar-x');
    if(x)x.addEventListener('click',function(){bar.style.display='none';document.body.classList.remove('nyse-bar-on');try{sessionStorage.setItem('nyseBar','1');}catch(e){}});
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
<div class="nyse-banner"><span class="nyse-b-tag">&#128085; {tag} &#128085;</span><span class="nyse-b-sub">{blurb}</span><a class="nyse-btn" href="{STORE_URL}" target="_blank" rel="noopener sponsored">{cta} &rarr;</a></div>
<!-- nyse:banner:end -->"""


def extras_html(lang):
    tag, blurb, cta = BANNER_TEXT[lang]
    a = f'href="{STORE_URL}" target="_blank" rel="noopener sponsored"'
    rail = lambda side: f'<a class="nyse-rail nyse-rail-{side}" {a}><span class="nyse-r-ico">&#128085;</span><span class="nyse-r-tag">{tag}</span><span class="nyse-btn">{cta}</span></a>'
    return f"""<!-- nyse:extras:start -->
{rail("l")}
{rail("r")}
<div class="nyse-bar" id="nyse-bar"><span>&#128085; {tag}</span><a class="nyse-btn" {a}>{cta} &rarr;</a><button class="nyse-bar-x" type="button" aria-label="Close">&times;</button></div>
<!-- nyse:extras:end -->
"""


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
    html = block("extras").sub("", html)
    extra = "" if is_nyc(rel, prefixes) else extras_html(lang)
    if re.search(r"</head>", html, re.I):
        html = re.sub(r"</head>", lambda m: css + m.group(0), html, count=1, flags=re.I)
    else:
        log.append("no </head> - CSS prepended"); html = css + html
    if re.search(r"</body>", html, re.I):
        html = re.sub(r"</body>", lambda m: extra + js + m.group(0), html, count=1, flags=re.I)
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
                html = html[:m.start()] + hdr + "\n" + html[m.end():]; done = True; break
        if not done:
            m = re.search(r"<nav\b.*?</nav>", html, re.S | re.I)
            if m:
                html = html[:m.start()] + hdr + "\n" + html[m.end():]; done = True; log.append("replaced <nav> (no <header> found)")
        if not done:
            html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + hdr + "\n", html, count=1, flags=re.I)
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