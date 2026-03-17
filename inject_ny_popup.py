import os
import re

FOLDER_PATH = "." 

def inject_popup(directory):
    files_fixed = 0
    skipped = 0
    
    # The universal popup code (HTML + JS) tailored for New York
    popup_code = """
<div id="ec-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:9998;align-items:center;justify-content:center;">
  <div id="ec-modal" style="background:#fff;border-radius:12px;padding:32px 28px;max-width:380px;width:90%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.18);">
    <button id="ec-close" aria-label="Close" style="position:absolute;top:12px;right:14px;background:none;border:none;font-size:20px;cursor:pointer;color:#888;line-height:1;">&#x2715;</button>
    <div id="ec-icon" style="font-size:28px;margin-bottom:10px;">📬</div>
    <h2 id="ec-title" style="margin:0 0 8px;font-size:18px;font-weight:600;color:#1a1a1a;"></h2>
    <p  id="ec-body"  style="margin:0 0 18px;font-size:14px;color:#555;line-height:1.5;"></p>
    <div id="ec-form-wrap">
      <input id="ec-email" type="email" placeholder="your@email.com"
        style="width:100%;box-sizing:border-box;padding:10px 12px;border:1.5px solid #ddd;border-radius:7px;font-size:14px;margin-bottom:10px;outline:none;"/>
      <button id="ec-submit"
        style="width:100%;padding:11px;background:#1a6fdb;color:#fff;border:none;border-radius:7px;font-size:14px;font-weight:600;cursor:pointer;transition:background .15s;">
        Get Free Updates
      </button>
    </div>
    <div id="ec-success" style="display:none;text-align:center;padding:8px 0;">
      <div style="font-size:28px;margin-bottom:8px;">✅</div>
      <p style="font-weight:600;color:#1a1a1a;margin:0 0 4px;">You're in!</p>
      <p style="font-size:13px;color:#555;margin:0;">Check your inbox for a confirmation.</p>
    </div>
    <p style="margin:10px 0 0;font-size:11px;color:#aaa;text-align:center;">No spam. Unsubscribe any time.</p>
  </div>
</div>

<script
  id="ec-script"
  data-site="new_york_special_ed"
  data-language="PAGE_LANGUAGE_PLACEHOLDER"
  data-delay="10000"
  data-api="https://email-capture-api-831148457361.us-central1.run.app">
(function() {
  var script   = document.getElementById("ec-script");
  var API_BASE = script.getAttribute("data-api");
  var SITE     = script.getAttribute("data-site");
  var LANG     = script.getAttribute("data-language") || "en";
  var DELAY    = parseInt(script.getAttribute("data-delay") || "10000", 10);

  var COPY = {
    en: {
      title: "Free NY Special Ed Updates",
      body:  "Get district-specific guides, CSE tips, and your rights — straight to your inbox."
    },
    es: {
      title: "Actualizaciones de Educación Especial NY",
      body:  "Recibe guías por distrito, consejos sobre CSE y tus derechos — directo a tu correo.",
      button: "Recibir Actualizaciones"
    }
  };

  var copy = COPY[LANG] || COPY.en;
  var STORAGE_KEY = "ec_dismissed_" + SITE + "_" + LANG;
  
  if (localStorage.getItem(STORAGE_KEY)) return;

  document.getElementById("ec-title").textContent  = copy.title;
  document.getElementById("ec-body").textContent   = copy.body;
  if (copy.button) {
    document.getElementById("ec-submit").textContent = copy.button;
  }

  var overlay = document.getElementById("ec-overlay");
  var emailEl = document.getElementById("ec-email");
  var submitEl = document.getElementById("ec-submit");

  setTimeout(function() {
    overlay.style.display = "flex";
    emailEl.focus();
  }, DELAY);

  function close() {
    overlay.style.display = "none";
    localStorage.setItem(STORAGE_KEY, "1");
  }

  document.getElementById("ec-close").addEventListener("click", close);
  overlay.addEventListener("click", function(e) { if (e.target === overlay) close(); });
  document.addEventListener("keydown", function(e) { if (e.key === "Escape") close(); });

  submitEl.addEventListener("click", function() {
    var email = emailEl.value.trim();
    if (!email || !email.includes("@")) {
      emailEl.style.borderColor = "#e53e3e";
      emailEl.focus();
      return;
    }
    emailEl.style.borderColor = "#ddd";
    submitEl.disabled = true;
    submitEl.textContent = "…";

    fetch(API_BASE + "/api/signup", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email:      email,
        site:       SITE,
        language:   LANG,
        source:     "newsletter_popup",
        page_url:   window.location.href,
        page_title: document.title
      })
    })
    .then(function(r) { return r.json(); })
    .then(function(res) {
      if (res.success) {
        document.getElementById("ec-form-wrap").style.display = "none";
        document.getElementById("ec-success").style.display   = "block";
        localStorage.setItem(STORAGE_KEY, "1");
        setTimeout(close, 3000);
      } else {
        submitEl.disabled = false;
        submitEl.textContent = copy.button || "Get Free Updates";
        alert(res.error || "Something went wrong. Please try again.");
      }
    })
    .catch(function() {
      submitEl.disabled = false;
      submitEl.textContent = copy.button || "Get Free Updates";
      alert("Network error. Please try again.");
    });
  });

  emailEl.addEventListener("keydown", function(e) { if (e.key === "Enter") submitEl.click(); });
})();
</script>
</body>"""

    print("🔍 Scanning New York site to inject universal email popup...")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Skip if the popup is already on this page!
                    if 'id="ec-script"' in content:
                        skipped += 1
                        continue
                        
                    # Determine language by looking at the HTML tag
                    lang = "es" if 'lang="es"' in content.lower() else "en"
                    
                    # Customize the popup block for this specific page's language
                    customized_popup = popup_code.replace("PAGE_LANGUAGE_PLACEHOLDER", lang)
                    
                    # Inject it right before the closing </body> tag
                    if "</body>" in content:
                        new_content = content.replace("</body>", customized_popup)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        files_fixed += 1
                        print(f"✅ Injected ({lang.upper()}): {filepath}")
                    else:
                        print(f"⚠️ No </body> tag found in {filepath}. Skipping.")
                        
                except Exception as e:
                    print(f"⚠️ Could not read {filepath}: {e}")

    print(f"\n🎉 Done! Successfully injected the popup into {files_fixed} pages (Skipped {skipped} already injected).")

if __name__ == "__main__":
    inject_popup(FOLDER_PATH)