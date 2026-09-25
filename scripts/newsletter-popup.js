(function() {
  var script   = document.getElementById("ec-script");
  var API_BASE = script.getAttribute("data-api");
  var SITE     = script.getAttribute("data-site")     || "new_york_special_ed";
  var LANG     = script.getAttribute("data-language") || "en";
  var DELAY    = parseInt(script.getAttribute("data-delay") || "10000", 10);

  var COPY = {
    en: {
      title:   "Know Your District.<br><em style='color:#e5c158;font-style:italic;'>Know Your Rights.</em>",
      body:    "Most NYC parents don't know what their district is required to provide — until it's too late.",
      checks:  [
        "District-specific CSE timelines & contacts",
        "IEP rights and evaluation deadlines",
        "What to say at your next meeting",
        "Real outcomes from parents in your district"
      ],
      button:  "Send Me Free District Updates"
    },
    es: {
      title:   "Conozca Su Distrito.<br><em style='color:#e5c158;font-style:italic;'>Sus Derechos.</em>",
      body:    "La mayoría de los padres de NYC no saben lo que su distrito está obligado a proveer.",
      checks:  [
        "Plazos del CSE y contactos por distrito",
        "Derechos del IEP y plazos de evaluación",
        "Qué decir en su próxima reunión",
        "Resultados reales de padres en su distrito"
      ],
      button:  "Recibir Actualizaciones Gratis"
    }
  };

  var copy = COPY[LANG] || COPY.en;
  var STORAGE_KEY = "ec_dismissed_" + SITE + "_" + LANG;
  if (localStorage.getItem(STORAGE_KEY)) return;

  /* -- Inject copy -- */
  document.getElementById("ec-title").innerHTML  = copy.title;
  document.getElementById("ec-body").textContent = copy.body;
  document.getElementById("ec-submit").textContent = copy.button;

  var list = document.getElementById("ec-checklist");
  copy.checks.forEach(function(item) {
    var li = document.createElement("li");
    li.style.cssText = "font-size:13px;color:#6b5f53;padding:5px 0 5px 20px;position:relative;";
    li.innerHTML = '<span style="position:absolute;left:0;font-family:\'Cormorant Garamond\',serif;font-size:16px;color:#d4af37;">§</span>' + item;
    list.appendChild(li);
  });

  var overlay  = document.getElementById("ec-overlay");
  var emailEl  = document.getElementById("ec-email");
  var submitEl = document.getElementById("ec-submit");

  /* -- Show after delay -- */
  setTimeout(function() {
    overlay.style.display = "flex";
    emailEl.focus();
  }, DELAY);

  /* -- Close -- */
  function close() {
    overlay.style.display = "none";
    localStorage.setItem(STORAGE_KEY, "1");
  }
  document.getElementById("ec-close").addEventListener("click", close);
  overlay.addEventListener("click", function(e) { if (e.target === overlay) close(); });
  document.addEventListener("keydown", function(e) { if (e.key === "Escape") close(); });

  /* -- Hover on button -- */
  submitEl.addEventListener("mouseover",  function() { this.style.background = "#a50b24"; });
  submitEl.addEventListener("mouseout",   function() { this.style.background = "#c8102e"; });
  submitEl.addEventListener("mouseover",  function() { this.style.background = "#a50b24"; });

  /* -- Submit -- */
  submitEl.addEventListener("click", function() {
    var email = emailEl.value.trim();
    if (!email || !email.includes("@")) {
      emailEl.style.borderColor = "#c8102e";
      emailEl.focus();
      return;
    }
    emailEl.style.borderColor = "#d6cbbf";
    submitEl.disabled    = true;
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
        page_title: document.title,
        district:   (document.querySelector("[data-district]") || {}).dataset && document.querySelector("[data-district]").dataset.district || null
      })
    })
    .then(function(r) { return r.json(); })
    .then(function(res) {
      if (res.success) {
        document.getElementById("ec-form-wrap").style.display = "none";
        document.getElementById("ec-success").style.display   = "block";
        localStorage.setItem(STORAGE_KEY, "1");
        setTimeout(close, 4000);
      } else {
        submitEl.disabled    = false;
        submitEl.textContent = copy.button;
        alert(res.error || "Something went wrong. Please try again.");
      }
    })
    .catch(function() {
      submitEl.disabled    = false;
      submitEl.textContent = copy.button;
      alert("Network error. Please try again.");
    });
  });

  emailEl.addEventListener("keydown", function(e) { if (e.key === "Enter") submitEl.click(); });
})();