#!/usr/bin/env python3
"""
NYC IEP Page Generator
======================
Generates programmatic SEO pages (English + Spanish) for all 32 NYC
school districts using the Anthropic Claude API.

Output structure:
  output/
    nyc-district-06-washington-heights.md          ← English
    es/
      nyc-district-06-washington-heights.md        ← Spanish

Usage:
  pip install anthropic
  export ANTHROPIC_API_KEY="sk-ant-..."
  python generate_iep_pages.py

Options (edit CONFIG below):
  - LANGUAGES   : ["en"], ["es"], or ["en", "es"]
  - CONCURRENCY : parallel API calls (2–4 recommended)
  - OUTPUT_DIR  : where files are written
  - DISTRICTS   : comment out any you want to skip
"""

import os
import time
import anthropic
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ──────────────────────────────────────────────
# CONFIG  ← edit these
# ──────────────────────────────────────────────
CONFIG = {
    "LANGUAGES":   ["en", "es"],   # "en", "es", or both
    "CONCURRENCY": 2,              # parallel API requests
    "OUTPUT_DIR":  "output",       # relative to this script
    "MODEL":       "claude-sonnet-4-20250514",
    "MAX_TOKENS":  2000,
}

# ──────────────────────────────────────────────
# ALL 32 NYC DISTRICTS
# ──────────────────────────────────────────────
DISTRICTS = [
    {"name": "NYC District 01 - Lower East Side / Chinatown",     "slug": "nyc-district-01-lower-east-side-chinatown"},
    {"name": "NYC District 02 - Tribeca / Greenwich Village",      "slug": "nyc-district-02-tribeca-greenwich-village"},
    {"name": "NYC District 03 - Upper West Side",                  "slug": "nyc-district-03-upper-west-side"},
    {"name": "NYC District 04 - East Harlem",                      "slug": "nyc-district-04-east-harlem"},
    {"name": "NYC District 05 - Central Harlem",                   "slug": "nyc-district-05-central-harlem"},
    {"name": "NYC District 06 - Washington Heights",               "slug": "nyc-district-06-washington-heights"},
    {"name": "NYC District 07 - South Bronx",                      "slug": "nyc-district-07-south-bronx"},
    {"name": "NYC District 08 - Hunts Point / Morrisania",         "slug": "nyc-district-08-hunts-point-morrisania"},
    {"name": "NYC District 09 - Tremont / Belmont",                "slug": "nyc-district-09-tremont-belmont"},
    {"name": "NYC District 10 - Fordham / Riverdale",              "slug": "nyc-district-10-fordham-riverdale"},
    {"name": "NYC District 11 - Pelham Parkway / Morris Park",     "slug": "nyc-district-11-pelham-parkway-morris-park"},
    {"name": "NYC District 12 - Wakefield / Williamsbridge",       "slug": "nyc-district-12-wakefield-williamsbridge"},
    {"name": "NYC District 13 - Brooklyn Heights / Fort Greene",   "slug": "nyc-district-13-brooklyn-heights-fort-greene"},
    {"name": "NYC District 14 - Williamsburg / Greenpoint",        "slug": "nyc-district-14-williamsburg-greenpoint"},
    {"name": "NYC District 15 - Park Slope / Red Hook",            "slug": "nyc-district-15-park-slope-red-hook"},
    {"name": "NYC District 16 - Bushwick / Bedford-Stuyvesant",    "slug": "nyc-district-16-bushwick-bedford-stuyvesant"},
    {"name": "NYC District 17 - Crown Heights / Flatbush",         "slug": "nyc-district-17-crown-heights-flatbush"},
    {"name": "NYC District 18 - Canarsie / Flatlands",             "slug": "nyc-district-18-canarsie-flatlands"},
    {"name": "NYC District 19 - East New York / Starrett City",    "slug": "nyc-district-19-east-new-york-starrett-city"},
    {"name": "NYC District 20 - Bay Ridge / Bensonhurst",          "slug": "nyc-district-20-bay-ridge-bensonhurst"},
    {"name": "NYC District 21 - Coney Island / Brighton Beach",    "slug": "nyc-district-21-coney-island-brighton-beach"},
    {"name": "NYC District 22 - Flatbush / Marine Park",           "slug": "nyc-district-22-flatbush-marine-park"},
    {"name": "NYC District 23 - Brownsville",                      "slug": "nyc-district-23-brownsville"},
    {"name": "NYC District 24 - Middle Village / Ridgewood",       "slug": "nyc-district-24-middle-village-ridgewood"},
    {"name": "NYC District 25 - Flushing / Whitestone",            "slug": "nyc-district-25-flushing-whitestone"},
    {"name": "NYC District 26 - Bayside / Little Neck",            "slug": "nyc-district-26-bayside-little-neck"},
    {"name": "NYC District 27 - Jamaica / Howard Beach",           "slug": "nyc-district-27-jamaica-howard-beach"},
    {"name": "NYC District 28 - Forest Hills / Richmond Hill",     "slug": "nyc-district-28-forest-hills-richmond-hill"},
    {"name": "NYC District 29 - Springfield Gardens / Hollis",     "slug": "nyc-district-29-springfield-gardens-hollis"},
    {"name": "NYC District 30 - Astoria / Long Island City",       "slug": "nyc-district-30-astoria-long-island-city"},
    {"name": "NYC District 31 - Staten Island",                    "slug": "nyc-district-31-staten-island"},
    {"name": "NYC District 32 - Bushwick",                         "slug": "nyc-district-32-bushwick"},
]


# ──────────────────────────────────────────────
# SYSTEM PROMPTS
# ──────────────────────────────────────────────
EN_SYSTEM = """You are an expert New York Special Education advocate with deep knowledge \
of IDEA, New York State Education Law, and the NYC DOE's Committee on Special Education \
(CSE) process. You write clear, empathetic, SEO-optimized content for parents navigating \
special education."""

ES_SYSTEM = """Eres un experto en educación especial en Nueva York, completamente bilingüe \
(inglés/español), con amplio conocimiento de la ley IDEA, la Ley de Educación del Estado \
de Nueva York y el proceso del Comité de Educación Especial (CSE) del NYC DOE. Escribes \
contenido claro, empático y optimizado para SEO para padres hispanos que navegan el sistema \
de educación especial."""


# ──────────────────────────────────────────────
# PROMPT BUILDERS
# ──────────────────────────────────────────────
def build_en_prompt(district: dict) -> str:
    name = district["name"]
    slug = district["slug"]
    return f"""Generate a programmatic SEO page in Markdown for the following district.

District: {name}
Slug: {slug}

Output ONLY valid Markdown with YAML frontmatter. No extra commentary.

Requirements:
1. YAML frontmatter with these exact keys:
   - district_name: "{name}"
   - slug: "{slug}"
   - page_type: what-is-an-iep
   - language: en
   - seo_title: (compelling, ~60 chars, include district name)
   - meta_description: (155 chars max, include district + IEP keywords)

2. H1 title: "What Is an IEP in {name}?"

3. An empathetic 2-paragraph intro explaining what an IEP is and why it matters \
for families in this neighborhood.

4. ## The IEP Process in {name}
   Step-by-step explanation of how the CSE (Committee on Special Education) works \
in NYC, with specific reference to this district's community context (demographics, \
languages spoken, community characteristics).

5. ## Who Attends the IEP Meeting
   A bullet list of required CSE team members and a sentence about parent rights.

6. ## Your Rights as a Parent in {name}
   IDEA rights, procedural safeguards, and NYC-specific parent protections.

7. ## Common IEP Services Available in NYC
   List 6–8 services with brief descriptions (speech therapy, OT, PT, ICT classes, etc.).

8. ## Next Steps for Parents
   3–5 actionable numbered steps.

9. ## Get Help Writing Your IEP Request Letter
   A strong CTA paragraph (3–4 sentences) ending with: \
"Use our **AI IEP Request Letter Generator** to create a professional, \
legally-grounded letter in minutes — tailored to your child and your district."
"""


def build_es_prompt(district: dict) -> str:
    name = district["name"]
    slug = district["slug"]
    return f"""Genera una página SEO programática en Markdown para el siguiente distrito.

Distrito: {name}
Slug: {slug}

Produce SOLO Markdown válido con frontmatter YAML. Sin comentarios adicionales.

Requisitos:
1. Frontmatter YAML con estas claves exactas:
   - district_name: "{name}"
   - slug: "{slug}"
   - page_type: que-es-un-iep
   - language: es
   - seo_title: (en español, ~60 caracteres, incluir nombre del distrito)
   - meta_description: (máximo 155 caracteres, en español)

2. Título H1: "¿Qué Es un IEP en {name}?"

3. Introducción empática de 2 párrafos en español explicando qué es un IEP \
(Programa de Educación Individualizada) y por qué es importante para las familias \
de esta comunidad. Menciona el contexto cultural específico de este vecindario.

4. ## El Proceso del IEP en {name}
   Paso a paso de cómo funciona el Comité de Educación Especial (CSE). \
Usa términos en español pero incluye acrónimos en inglés (ej: IEP, CSE).

5. ## Quiénes Asisten a la Reunión del IEP
   Lista de miembros requeridos del equipo CSE. Menciona el derecho a \
un intérprete gratuito.

6. ## Sus Derechos como Padre o Madre en {name}
   Derechos bajo IDEA, salvaguardas procesales y protecciones de NYC. \
Incluye el derecho a comunicación en idioma nativo.

7. ## Servicios Comunes del IEP Disponibles en NYC
   Lista de 6–8 servicios con descripciones breves.

8. ## Próximos Pasos para los Padres
   3–5 pasos numerados y accionables.

9. ## Obtenga Ayuda para Escribir Su Carta de Solicitud de IEP
   Párrafo de llamada a la acción (3–4 oraciones) que termine con: \
"Use nuestro **Generador de Cartas IEP con IA** para crear una carta profesional \
y legalmente fundamentada en minutos — personalizada para su hijo y su distrito."
"""


# ──────────────────────────────────────────────
# API CALL
# ──────────────────────────────────────────────
def generate_page(client: anthropic.Anthropic, district: dict, lang: str) -> tuple[str, str]:
    """Returns (output_path, content). Raises on API error."""
    system  = EN_SYSTEM if lang == "en" else ES_SYSTEM
    prompt  = build_en_prompt(district) if lang == "en" else build_es_prompt(district)

    message = client.messages.create(
        model      = CONFIG["MODEL"],
        max_tokens = CONFIG["MAX_TOKENS"],
        system     = system,
        messages   = [{"role": "user", "content": prompt}],
    )
    content = message.content[0].text

    # Build file path
    filename = f"{district['slug']}.md"
    if lang == "es":
        filepath = Path(CONFIG["OUTPUT_DIR"]) / "es" / filename
    else:
        filepath = Path(CONFIG["OUTPUT_DIR"]) / filename

    return str(filepath), content


# ──────────────────────────────────────────────
# WRITE FILE
# ──────────────────────────────────────────────
def write_file(filepath: str, content: str) -> None:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("❌  Set ANTHROPIC_API_KEY environment variable first.")

    client = anthropic.Anthropic(api_key=api_key)

    # Build task list
    tasks = [
        (district, lang)
        for district in DISTRICTS
        for lang in CONFIG["LANGUAGES"]
    ]

    total     = len(tasks)
    done      = 0
    errors    = []

    print(f"\n🚀  Generating {total} pages "
          f"({len(DISTRICTS)} districts × {len(CONFIG['LANGUAGES'])} language(s))")
    print(f"    Concurrency: {CONFIG['CONCURRENCY']}  |  Output: {CONFIG['OUTPUT_DIR']}/\n")

    start = time.time()

    def process(task):
        district, lang = task
        try:
            filepath, content = generate_page(client, district, lang)
            write_file(filepath, content)
            return ("ok", filepath)
        except Exception as exc:
            return ("error", f"{district['slug']} [{lang}]: {exc}")

    with ThreadPoolExecutor(max_workers=CONFIG["CONCURRENCY"]) as pool:
        futures = {pool.submit(process, t): t for t in tasks}
        for future in as_completed(futures):
            status, info = future.result()
            done += 1
            pct  = int(done / total * 100)
            bar  = ("█" * (pct // 5)).ljust(20)
            if status == "ok":
                print(f"  [{bar}] {pct:3d}%  ✅  {info}")
            else:
                errors.append(info)
                print(f"  [{bar}] {pct:3d}%  ❌  {info}")

    elapsed = time.time() - start
    print(f"\n{'─'*60}")
    print(f"  Done in {elapsed:.1f}s  |  {done - len(errors)}/{total} succeeded")
    if errors:
        print(f"\n  Failed ({len(errors)}):")
        for e in errors:
            print(f"    • {e}")
    print(f"\n  Files written to: {Path(CONFIG['OUTPUT_DIR']).resolve()}/\n")


if __name__ == "__main__":
    main()