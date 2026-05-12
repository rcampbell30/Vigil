"""
generate_site.py - Generates index.html for the exohabitability website.

Reads data/latest.csv (produced by scraper.py), scores all planets using
habitability.py, and writes a fully self-contained index.html that GitHub
Pages can serve as a static site.

If no CSV is found it falls back to built-in sample data so the site renders
correctly straight from a fresh clone before the first scrape has run.

Run this after scraper.py each year, or let the GitHub Actions workflow do it.

Author: Rory
"""

import csv
import json
import os
from datetime import datetime
from habitability import score_planet, top_n, _safe_float

# ---------------------------------------------------------------------------
# Sample data - used when data/latest.csv does not exist yet.
# Values are from the NASA Exoplanet Archive as of 2025.
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    {"pl_name":"Kepler-442 b",  "hostname":"Kepler-442",    "sy_dist":"342",  "pl_rade":"1.34", "pl_masse":"2.3",  "pl_orbper":"112.3",  "pl_orbsmax":"0.409",  "st_teff":"4402",  "st_lum":"-0.951", "st_age":"2.9",  "disc_year":"2015", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"Kepler-452 b",  "hostname":"Kepler-452",    "sy_dist":"430",  "pl_rade":"1.63", "pl_masse":"5.0",  "pl_orbper":"384.8",  "pl_orbsmax":"1.046",  "st_teff":"5757",  "st_lum":"0.079",  "st_age":"6.0",  "disc_year":"2015", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"TOI-700 d",     "hostname":"TOI-700",       "sy_dist":"31.1", "pl_rade":"1.19", "pl_masse":"1.57", "pl_orbper":"37.4",   "pl_orbsmax":"0.163",  "st_teff":"3480",  "st_lum":"-1.633", "st_age":"1.5",  "disc_year":"2020", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"Kepler-62 f",   "hostname":"Kepler-62",     "sy_dist":"990",  "pl_rade":"1.41", "pl_masse":"2.8",  "pl_orbper":"267.3",  "pl_orbsmax":"0.718",  "st_teff":"4925",  "st_lum":"-0.677", "st_age":"7.0",  "disc_year":"2013", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"Kepler-1229 b", "hostname":"Kepler-1229",   "sy_dist":"770",  "pl_rade":"1.4",  "pl_masse":"",     "pl_orbper":"86.8",   "pl_orbsmax":"0.34",   "st_teff":"3784",  "st_lum":"-1.570", "st_age":"",     "disc_year":"2016", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"GJ 667C c",     "hostname":"GJ 667C",       "sy_dist":"6.8",  "pl_rade":"1.5",  "pl_masse":"3.8",  "pl_orbper":"28.1",   "pl_orbsmax":"0.125",  "st_teff":"3350",  "st_lum":"-1.921", "st_age":"",     "disc_year":"2011", "discoverymethod":"Radial Velocity", "pl_controv_flag":"0"},
    {"pl_name":"TRAPPIST-1 e",  "hostname":"TRAPPIST-1",    "sy_dist":"12.1", "pl_rade":"0.92", "pl_masse":"0.69", "pl_orbper":"6.1",    "pl_orbsmax":"0.0293", "st_teff":"2566",  "st_lum":"-3.283", "st_age":"7.6",  "disc_year":"2017", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"TRAPPIST-1 f",  "hostname":"TRAPPIST-1",    "sy_dist":"12.1", "pl_rade":"1.04", "pl_masse":"1.04", "pl_orbper":"9.2",    "pl_orbsmax":"0.0385", "st_teff":"2566",  "st_lum":"-3.283", "st_age":"7.6",  "disc_year":"2017", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"Proxima Cen b", "hostname":"Proxima Centauri","sy_dist":"1.3","pl_rade":"1.1",  "pl_masse":"1.07", "pl_orbper":"11.2",   "pl_orbsmax":"0.0485", "st_teff":"3050",  "st_lum":"-2.810", "st_age":"4.85", "disc_year":"2016", "discoverymethod":"Radial Velocity", "pl_controv_flag":"0"},
    {"pl_name":"Kepler-296 e",  "hostname":"Kepler-296",    "sy_dist":"682",  "pl_rade":"1.48", "pl_masse":"",     "pl_orbper":"34.1",   "pl_orbsmax":"0.165",  "st_teff":"3740",  "st_lum":"-1.598", "st_age":"",     "disc_year":"2014", "discoverymethod":"Transit", "pl_controv_flag":"0"},
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_planets() -> tuple[list[dict], str]:
    """Load planet data from CSV if available, otherwise use sample data.

    :return: Tuple of (list of planet dicts, data source description string).
    """
    latest_path = os.path.join("data", "latest.csv")

    if os.path.exists(latest_path):
        with open(latest_path, newline="", encoding="utf-8") as f:
            planets = list(csv.DictReader(f))
        source = f"NASA Exoplanet Archive — {len(planets):,} confirmed planets"
        return planets, source

    # Fall back to sample data
    print("No data/latest.csv found - using built-in sample data.")
    print("Run scraper.py first to get the full dataset.")
    source = "Sample data (run scraper.py to load the full NASA archive)"
    return SAMPLE_ROWS, source


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def score_color(score: float) -> str:
    """Map a 0-10 score to a CSS colour, red -> amber -> teal."""
    if score >= 7.5:
        return "#3af7b5"   # Teal - good
    elif score >= 5.0:
        return "#f7c948"   # Amber - moderate
    else:
        return "#f75a3a"   # Red-orange - poor


def render_score_bar(label: str, score, is_magnetic: bool = False) -> str:
    """Render one score bar row as HTML."""
    if score is None:
        pct = 0
        score_str = "N/A"
        color = "#2a3a52"
    else:
        score_rounded = round(score, 1)
        pct = score / 10 * 100
        score_str = f"{score_rounded}"
        color = "#ff8c42" if is_magnetic else score_color(score)

    magnetic_label = " ★" if is_magnetic else ""
    return f"""
        <div class="score-row">
          <span class="score-label">{label}{magnetic_label}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct:.1f}%;background:{color};"></div>
          </div>
          <span class="score-val" style="color:{color};">{score_str}</span>
        </div>"""


def render_planet_card(rank: int, planet: dict) -> str:
    """Render one planet card as HTML."""
    name        = planet["pl_name"]
    host        = planet["hostname"]
    dist        = planet.get("sy_dist_pc")
    dist_str    = f"{float(dist):.0f} pc" if dist else "dist unknown"
    disc        = planet.get("disc_year", "")
    comp        = planet.get("composite_score")
    comp_str    = f"{comp:.2f}" if comp is not None else "—"
    comp_color  = score_color(comp) if comp else "#2a3a52"
    comp_pct    = (comp / 10 * 100) if comp else 0
    # SVG circle gauge: circumference of r=40 circle = 2*pi*40 ≈ 251.3
    circ        = 251.3
    dash_fill   = circ * comp_pct / 100
    missing     = planet.get("missing_data", "")
    missing_note = f'<p class="missing">⚠ missing data: {missing}</p>' if missing and missing != "none" else ""

    bars = (
        render_score_bar("Magnetic Field", planet.get("score_magnetic_field"), is_magnetic=True) +
        render_score_bar("Habitable Zone", planet.get("score_habitable_zone")) +
        render_score_bar("Rocky Surface",  planet.get("score_rocky_likelihood")) +
        render_score_bar("Stellar Stability", planet.get("score_stellar_stability")) +
        render_score_bar("System Age",     planet.get("score_system_age")) +
        render_score_bar("Atmos. Retention", planet.get("score_atmosphere_hold"))
    )

    return f"""
  <article class="card" style="--rank-color:{comp_color};">
    <div class="card-rank">{rank:02d}</div>
    <div class="card-body">
      <div class="card-header">
        <div class="card-names">
          <h2 class="planet-name">{name}</h2>
          <p class="planet-meta">{host} &nbsp;·&nbsp; {dist_str} &nbsp;·&nbsp; disc. {disc}</p>
          {missing_note}
        </div>
        <div class="composite-gauge">
          <svg viewBox="0 0 100 100" width="90" height="90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#1a2535" stroke-width="8"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="{comp_color}" stroke-width="8"
              stroke-dasharray="{dash_fill:.1f} {circ:.1f}"
              stroke-dashoffset="{circ * 0.25:.1f}"
              stroke-linecap="round"/>
            <text x="50" y="50" text-anchor="middle" dy="0.35em"
              font-family="'JetBrains Mono',monospace" font-size="16"
              fill="{comp_color}" font-weight="700">{comp_str}</text>
          </svg>
          <p class="gauge-label">composite</p>
        </div>
      </div>
      <div class="score-bars">{bars}</div>
    </div>
  </article>"""


def generate_html(planets_raw: list[dict], source: str) -> str:
    """Generate the full index.html as a string."""
    # Score and take top 10
    results    = top_n(planets_raw, n=10)
    updated    = datetime.now().strftime("%d %B %Y")
    total_scored = len([p for p in planets_raw])

    # Render all cards
    cards_html = "".join(render_planet_card(i + 1, p) for i, p in enumerate(results))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Vigil — The Long Watch</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet"/>
  <style>
    /* ── Reset & base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:        #070b12;
      --bg2:       #0d1420;
      --bg3:       #111c2e;
      --border:    #1e2e44;
      --text:      #c4d0e3;
      --text-dim:  #566880;
      --teal:      #3af7b5;
      --amber:     #ff8c42;
      --red:       #f75a3a;
      --white:     #e8eef8;
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      line-height: 1.6;
      min-height: 100vh;
      overflow-x: hidden;
    }}

    /* ── Starfield ── */
    #stars {{
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background:
        radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 23% 67%, rgba(255,255,255,.45) 0%, transparent 100%),
        radial-gradient(1px 1px at 38% 32%, rgba(255,255,255,.6)  0%, transparent 100%),
        radial-gradient(1px 1px at 52% 80%, rgba(255,255,255,.4)  0%, transparent 100%),
        radial-gradient(1px 1px at 67% 20%, rgba(255,255,255,.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 79% 55%, rgba(255,255,255,.5)  0%, transparent 100%),
        radial-gradient(1px 1px at 88% 8%,  rgba(255,255,255,.65) 0%, transparent 100%),
        radial-gradient(1px 1px at 95% 75%, rgba(255,255,255,.4)  0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 5%  90%, rgba(255,255,255,.35) 0%, transparent 100%),
        radial-gradient(1px 1px at 44% 48%, rgba(255,255,255,.5)  0%, transparent 100%),
        radial-gradient(1px 1px at 17% 40%, rgba(255,255,255,.3)  0%, transparent 100%),
        radial-gradient(1px 1px at 61% 62%, rgba(255,255,255,.45) 0%, transparent 100%),
        radial-gradient(1px 1px at 82% 33%, rgba(255,255,255,.5)  0%, transparent 100%),
        radial-gradient(1px 1px at 30% 88%, rgba(255,255,255,.35) 0%, transparent 100%),
        radial-gradient(2px 2px at 70% 10%, rgba(180,220,255,.4)  0%, transparent 100%),
        radial-gradient(1px 1px at 55% 5%,  rgba(255,255,255,.6)  0%, transparent 100%),
        var(--bg);
    }}

    /* ── Layout wrapper ── */
    .wrapper {{ position: relative; z-index: 1; max-width: 900px; margin: 0 auto; padding: 0 1.5rem 4rem; }}

    /* ── Header ── */
    header {{
      padding: 5rem 0 3rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 3rem;
    }}

    .header-eyebrow {{
      font-size: 11px; letter-spacing: .2em; text-transform: uppercase;
      color: var(--teal); margin-bottom: 1rem;
    }}

    h1 {{
      font-family: 'Libre Baskerville', serif;
      font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 700; color: var(--white);
      line-height: 1.1; margin-bottom: 1.25rem;
    }}

    h1 em {{ font-style: italic; color: var(--teal); }}

    .header-desc {{
      font-family: 'Libre Baskerville', serif;
      font-size: 1rem; color: var(--text);
      max-width: 620px; line-height: 1.8;
      margin-bottom: 2rem;
    }}

    .header-meta {{
      display: flex; flex-wrap: wrap; gap: 2rem;
      font-size: 11px; letter-spacing: .12em;
      text-transform: uppercase; color: var(--text-dim);
    }}

    .header-meta span {{ display: flex; align-items: center; gap: .5rem; }}
    .header-meta strong {{ color: var(--teal); }}

    /* ── Section title ── */
    .section-title {{
      font-family: 'Libre Baskerville', serif;
      font-size: .8rem; letter-spacing: .18em;
      text-transform: uppercase; color: var(--text-dim);
      margin-bottom: 1.5rem;
      display: flex; align-items: center; gap: 1rem;
    }}
    .section-title::after {{
      content: ''; flex: 1; height: 1px; background: var(--border);
    }}

    /* ── Planet cards ── */
    .cards {{ display: flex; flex-direction: column; gap: 1.25rem; }}

    .card {{
      background: var(--bg2);
      border: 1px solid var(--border);
      border-left: 3px solid var(--rank-color, var(--teal));
      border-radius: 4px;
      display: flex; align-items: stretch;
      transition: border-color .2s, box-shadow .2s;
      animation: fadeUp .5s ease both;
    }}

    .card:hover {{
      box-shadow: 0 0 30px rgba(58,247,181,.07);
      border-color: var(--rank-color, var(--teal));
    }}

    @keyframes fadeUp {{
      from {{ opacity:0; transform: translateY(12px); }}
      to   {{ opacity:1; transform: translateY(0); }}
    }}

    /* Stagger card animations */
    .card:nth-child(1)  {{ animation-delay: .05s; }}
    .card:nth-child(2)  {{ animation-delay: .10s; }}
    .card:nth-child(3)  {{ animation-delay: .15s; }}
    .card:nth-child(4)  {{ animation-delay: .20s; }}
    .card:nth-child(5)  {{ animation-delay: .25s; }}
    .card:nth-child(6)  {{ animation-delay: .30s; }}
    .card:nth-child(7)  {{ animation-delay: .35s; }}
    .card:nth-child(8)  {{ animation-delay: .40s; }}
    .card:nth-child(9)  {{ animation-delay: .45s; }}
    .card:nth-child(10) {{ animation-delay: .50s; }}

    .card-rank {{
      width: 56px; min-width: 56px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.6rem; font-weight: 700;
      color: var(--border);
      border-right: 1px solid var(--border);
      user-select: none;
    }}

    .card-body {{ flex: 1; padding: 1.25rem 1.5rem; }}

    .card-header {{
      display: flex; align-items: flex-start;
      justify-content: space-between; gap: 1rem;
      margin-bottom: 1rem;
    }}

    .planet-name {{
      font-family: 'Libre Baskerville', serif;
      font-size: 1.3rem; color: var(--white);
      font-weight: 700; margin-bottom: .2rem;
    }}

    .planet-meta {{
      font-size: 11px; color: var(--text-dim);
      letter-spacing: .05em;
    }}

    .missing {{
      font-size: 10px; color: #6a4e35;
      margin-top: .3rem; letter-spacing: .04em;
    }}

    /* Composite gauge */
    .composite-gauge {{ text-align: center; flex-shrink: 0; }}
    .composite-gauge svg {{ display: block; }}
    .gauge-label {{
      font-size: 9px; letter-spacing: .14em;
      text-transform: uppercase; color: var(--text-dim);
      margin-top: .2rem;
    }}

    /* Score bars */
    .score-bars {{ display: flex; flex-direction: column; gap: .45rem; }}

    .score-row {{
      display: grid;
      grid-template-columns: 140px 1fr 38px;
      align-items: center; gap: .6rem;
    }}

    .score-label {{
      font-size: 10px; letter-spacing: .06em;
      text-transform: uppercase; color: var(--text-dim);
      white-space: nowrap;
    }}

    .bar-track {{
      height: 5px; background: var(--bg3);
      border-radius: 3px; overflow: hidden;
    }}

    .bar-fill {{
      height: 100%; border-radius: 3px;
      transition: width 1s cubic-bezier(.22,1,.36,1);
      animation: growBar 1.2s cubic-bezier(.22,1,.36,1) both;
    }}

    @keyframes growBar {{
      from {{ width: 0 !important; }}
    }}

    .score-val {{
      font-size: 11px; font-weight: 600;
      text-align: right;
    }}

    /* ── Methodology section ── */
    .methodology {{
      margin-top: 4rem; padding-top: 2rem;
      border-top: 1px solid var(--border);
    }}

    .methodology h3 {{
      font-family: 'Libre Baskerville', serif;
      font-size: 1rem; color: var(--white);
      margin-bottom: 1rem;
    }}

    .method-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem; margin-top: 1rem;
    }}

    .method-item {{
      background: var(--bg2); border: 1px solid var(--border);
      border-radius: 4px; padding: 1rem;
    }}

    .method-item h4 {{
      font-size: 10px; letter-spacing: .12em;
      text-transform: uppercase; margin-bottom: .4rem;
    }}

    .method-item h4.magnetic {{ color: var(--amber); }}
    .method-item h4.other    {{ color: var(--teal); }}

    .method-item p {{
      font-family: 'Libre Baskerville', serif;
      font-size: .8rem; color: var(--text-dim); line-height: 1.6;
    }}

    /* ── Footer ── */
    footer {{
      margin-top: 3rem; padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      font-size: 10px; letter-spacing: .08em;
      color: var(--text-dim);
      display: flex; flex-wrap: wrap; gap: 1rem;
      justify-content: space-between; align-items: center;
    }}

    footer a {{ color: var(--teal); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}

    /* ── Responsive ── */
    @media (max-width: 600px) {{
      .card-header {{ flex-direction: column; }}
      .composite-gauge {{ align-self: flex-end; }}
      .score-row {{ grid-template-columns: 110px 1fr 32px; }}
      .card-rank {{ width: 36px; min-width: 36px; font-size: 1rem; }}
    }}
  </style>
</head>
<body>
  <div id="stars"></div>
  <div class="wrapper">

    <header>
      <p class="header-eyebrow">Vigil &nbsp;/&nbsp; Exoplanet Habitability Index &nbsp;/&nbsp; SETI Targeting</p>
      <h1>The Long<br/><em>Watch.</em></h1>
      <p class="header-desc">
        A ranked catalogue of confirmed exoplanets scored across six physical
        habitability dimensions — including magnetic field likelihood, the most
        underappreciated filter in the search for life.  Updated automatically
        each year from the NASA Exoplanet Archive.
      </p>
      <div class="header-meta">
        <span>Data source: <strong>NASA Exoplanet Archive</strong></span>
        <span>Updated: <strong>{updated}</strong></span>
        <span>Source: <strong>{source}</strong></span>
      </div>
    </header>

    <p class="section-title">Top 10 Candidates</p>

    <div class="cards">
      {cards_html}
    </div>

    <section class="methodology">
      <h3>Scoring Methodology</h3>
      <p style="font-family:'Libre Baskerville',serif;font-size:.85rem;
                color:var(--text-dim);line-height:1.8;max-width:680px;margin-bottom:1rem;">
        Each planet is scored 0–10 across six dimensions using physical models
        derived from published habitability research.  The composite score is a
        weighted average (missing data dimensions are excluded and weights
        redistributed).  The ★ magnetic field score carries the highest individual
        weight (25%) as a shieldless planet loses its atmosphere to stellar wind
        over geological timescales.
      </p>
      <div class="method-grid">
        <div class="method-item">
          <h4 class="magnetic">★ Magnetic Field (25%)</h4>
          <p>Inferred from planet mass, bulk density, tidal locking risk, and system age.
             Requires an active liquid iron core dynamo. Peaks ~2 Earth masses.</p>
        </div>
        <div class="method-item">
          <h4 class="other">Habitable Zone (25%)</h4>
          <p>Computed from stellar luminosity and orbital distance using the
             Kopparapu et al. 2013 model.  Scores peak at the centre of the zone.</p>
        </div>
        <div class="method-item">
          <h4 class="other">Rocky Surface (20%)</h4>
          <p>Radius below the Fulton gap (~1.5 R⊕) indicates a rocky world rather
             than a mini-Neptune with a thick H/He envelope.</p>
        </div>
        <div class="method-item">
          <h4 class="other">Stellar Stability (15%)</h4>
          <p>G and K dwarfs score highest — long-lived, low UV, stable output.
             M dwarfs penalised for flaring; O/B/A stars for short lifespans.</p>
        </div>
        <div class="method-item">
          <h4 class="other">System Age (10%)</h4>
          <p>Complex life took ~4 Gyr on Earth.  Young systems haven't had time;
             very old systems may have geologically dead planets.</p>
        </div>
        <div class="method-item">
          <h4 class="other">Atmosphere Retention (5%)</h4>
          <p>Escape velocity proxy from mass and radius.  Mars-like planets lose
             atmospheres over Gyr timescales.  Peaks at Earth-like values.</p>
        </div>
      </div>
    </section>

    <footer>
      <span>Data: <a href="https://exoplanetarchive.ipac.caltech.edu" target="_blank">NASA Exoplanet Archive</a></span>
      <span>HZ model: Kopparapu et al. 2013</span>
      <span>Vigil — built by Rory &nbsp;·&nbsp; runs forever</span>
    </footer>

  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    planets_raw, source = load_planets()
    print(f"Loaded {len(planets_raw)} planets from: {source}")
    print("Scoring...")
    html = generate_html(planets_raw, source)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated index.html ({len(html):,} bytes)")
    print("Deploy the repo to GitHub Pages and you're live.")


if __name__ == "__main__":
    main()
