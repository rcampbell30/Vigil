"""
generate_site.py - Generates index.html for the Vigil exoplanet habitability site.

Reads data/latest.csv (produced by scraper.py), scores all planets using
habitability.py, and writes a self-contained static index.html for GitHub Pages.

If no CSV is found, it falls back to built-in sample data so the site renders
from a fresh clone.

Author: Rory
"""

import csv
import html
import os
from datetime import datetime
from habitability import top_n


SAMPLE_ROWS = [
    {"pl_name":"Kepler-442 b", "hostname":"Kepler-442", "sy_dist":"342", "pl_rade":"1.34", "pl_masse":"2.3", "pl_orbper":"112.3", "pl_orbsmax":"0.409", "pl_eqt":"233", "st_teff":"4402", "st_lum":"-0.951", "st_age":"2.9", "disc_year":"2015", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"TOI-700 d", "hostname":"TOI-700", "sy_dist":"31.1", "pl_rade":"1.19", "pl_masse":"1.57", "pl_orbper":"37.4", "pl_orbsmax":"0.163", "pl_eqt":"269", "st_teff":"3480", "st_lum":"-1.633", "st_age":"1.5", "disc_year":"2020", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"Proxima Cen b", "hostname":"Proxima Centauri", "sy_dist":"1.3", "pl_rade":"1.1", "pl_masse":"1.07", "pl_orbper":"11.2", "pl_orbsmax":"0.0485", "pl_eqt":"234", "st_teff":"3050", "st_lum":"-2.810", "st_age":"4.85", "disc_year":"2016", "discoverymethod":"Radial Velocity", "pl_controv_flag":"0"},
    {"pl_name":"TRAPPIST-1 e", "hostname":"TRAPPIST-1", "sy_dist":"12.1", "pl_rade":"0.92", "pl_masse":"0.69", "pl_orbper":"6.1", "pl_orbsmax":"0.0293", "pl_eqt":"251", "st_teff":"2566", "st_lum":"-3.283", "st_age":"7.6", "disc_year":"2017", "discoverymethod":"Transit", "pl_controv_flag":"0"},
    {"pl_name":"Kepler-62 f", "hostname":"Kepler-62", "sy_dist":"990", "pl_rade":"1.41", "pl_masse":"2.8", "pl_orbper":"267.3", "pl_orbsmax":"0.718", "pl_eqt":"208", "st_teff":"4925", "st_lum":"-0.677", "st_age":"7.0", "disc_year":"2013", "discoverymethod":"Transit", "pl_controv_flag":"0"},
]


def load_planets() -> tuple[list[dict], str]:
    """Load scraped NASA data if present, otherwise use sample data."""
    latest_path = os.path.join("data", "latest.csv")

    if os.path.exists(latest_path):
        with open(latest_path, newline="", encoding="utf-8") as f:
            planets = list(csv.DictReader(f))
        return planets, f"NASA Exoplanet Archive — {len(planets):,} confirmed planets"

    print("No data/latest.csv found - using built-in sample data.")
    return SAMPLE_ROWS, "Sample data (run scraper.py to load the full NASA archive)"


def esc(value) -> str:
    """HTML-escape display values."""
    return html.escape("" if value is None else str(value), quote=True)


def score_color(score) -> str:
    """Map a 0-10 score to red, amber, or teal."""
    if score is None:
        return "#2a3a52"
    if score >= 7.5:
        return "#3af7b5"
    if score >= 5.0:
        return "#f7c948"
    return "#f75a3a"


def fmt_score(score) -> str:
    """Format a score for display."""
    return "N/A" if score is None else f"{score:.1f}"


def render_score_bar(label: str, score, modifier: str = "") -> str:
    """Render one score bar row as HTML."""
    pct = 0 if score is None else max(0, min(100, score * 10))
    color = "#ff8c42" if modifier == "magnetic" and score is not None else score_color(score)
    label_extra = " ★" if modifier == "magnetic" else ""
    value = fmt_score(score)

    return f"""
        <div class="score-row">
          <span class="score-label">{esc(label)}{label_extra}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct:.1f}%;background:{color};"></div>
          </div>
          <span class="score-val" style="color:{color};">{value}</span>
        </div>"""


def render_badges(planet: dict) -> str:
    """Render risk/missing badges."""
    badges = []

    flags = planet.get("risk_flags", "")
    if flags and flags != "none":
        badges.extend(flag.strip() for flag in flags.split(",") if flag.strip())

    missing = planet.get("missing_data", "")
    if missing and missing != "none":
        badges.append(f"missing: {missing}")

    if not badges:
        return ""

    return '<div class="badges">' + "".join(f'<span class="badge">{esc(b)}</span>' for b in badges[:5]) + "</div>"


def render_planet_card(rank: int, planet: dict) -> str:
    """Render one planet card."""
    name = esc(planet["pl_name"])
    host = esc(planet["hostname"])
    dist = planet.get("sy_dist_pc")
    dist_str = f"{float(dist):.0f} pc" if dist else "dist unknown"
    disc = esc(planet.get("disc_year", ""))

    comp = planet.get("composite_score")
    comp_str = "—" if comp is None else f"{comp:.2f}"
    comp_color = score_color(comp)
    comp_pct = 0 if comp is None else max(0, min(100, comp * 10))

    circ = 251.3
    dash_fill = circ * comp_pct / 100

    evidence = planet.get("evidence_score")
    confidence = planet.get("data_confidence_score")
    ceiling = planet.get("habitability_ceiling")
    rank_type = "ranked" if planet.get("rankable") else "watchlist"

    bars = (
        render_score_bar("Magnetic Field", planet.get("score_magnetic_field"), "magnetic") +
        render_score_bar("Habitable Zone", planet.get("score_habitable_zone")) +
        render_score_bar("Thermal Plausibility", planet.get("score_thermal_plausibility")) +
        render_score_bar("Rocky Surface", planet.get("score_rocky_likelihood")) +
        render_score_bar("Stellar Stability", planet.get("score_stellar_stability")) +
        render_score_bar("System Age", planet.get("score_system_age")) +
        render_score_bar("Atmos. Retention", planet.get("score_atmosphere_hold")) +
        render_score_bar("Data Confidence", confidence)
    )

    evidence_text = "N/A" if evidence is None else f"{evidence:.2f}"
    confidence_text = "N/A" if confidence is None else f"{confidence:.1f}"
    ceiling_text = "N/A" if ceiling is None else f"{ceiling:.1f}"

    return f"""
  <article class="card" style="--rank-color:{comp_color};">
    <div class="card-rank">{rank:02d}</div>
    <div class="card-body">
      <div class="card-header">
        <div class="card-names">
          <p class="rank-type">{rank_type}</p>
          <h2 class="planet-name">{name}</h2>
          <p class="planet-meta">{host} &nbsp;·&nbsp; {dist_str} &nbsp;·&nbsp; disc. {disc}</p>
          {render_badges(planet)}
        </div>
        <div class="composite-gauge">
          <svg viewBox="0 0 100 100" width="92" height="92">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#1a2535" stroke-width="8"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="{comp_color}" stroke-width="8"
              stroke-dasharray="{dash_fill:.1f} {circ:.1f}"
              stroke-dashoffset="{circ * 0.25:.1f}"
              stroke-linecap="round"/>
            <text x="50" y="50" text-anchor="middle" dy="0.35em"
              font-family="'JetBrains Mono',monospace" font-size="16"
              fill="{comp_color}" font-weight="700">{comp_str}</text>
          </svg>
          <p class="gauge-label">Vigil score</p>
        </div>
      </div>

      <div class="score-summary">
        <span>Evidence <strong>{evidence_text}</strong></span>
        <span>Confidence <strong>{confidence_text}</strong></span>
        <span>Ceiling <strong>{ceiling_text}</strong></span>
      </div>

      <div class="score-bars">{bars}</div>
    </div>
  </article>"""


def generate_html(planets_raw: list[dict], source: str) -> str:
    """Generate the full static site."""
    results = top_n(planets_raw, n=10)
    updated = datetime.now().strftime("%d %B %Y")
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
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:#070b12; --bg2:#0d1420; --bg3:#111c2e; --border:#1e2e44;
      --text:#c4d0e3; --text-dim:#566880; --teal:#3af7b5;
      --amber:#ff8c42; --red:#f75a3a; --white:#e8eef8;
    }}

    html {{ scroll-behavior: smooth; }}
    body {{
      background: var(--bg); color: var(--text);
      font-family: 'JetBrains Mono', monospace; font-size: 14px;
      line-height: 1.6; min-height: 100vh; overflow-x: hidden;
    }}

    #stars {{
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background:
        radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 23% 67%, rgba(255,255,255,.45) 0%, transparent 100%),
        radial-gradient(1px 1px at 38% 32%, rgba(255,255,255,.6) 0%, transparent 100%),
        radial-gradient(1px 1px at 52% 80%, rgba(255,255,255,.4) 0%, transparent 100%),
        radial-gradient(1px 1px at 67% 20%, rgba(255,255,255,.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 79% 55%, rgba(255,255,255,.5) 0%, transparent 100%),
        radial-gradient(1px 1px at 88% 8%, rgba(255,255,255,.65) 0%, transparent 100%),
        radial-gradient(1px 1px at 95% 75%, rgba(255,255,255,.4) 0%, transparent 100%),
        var(--bg);
    }}

    .wrapper {{ position: relative; z-index: 1; max-width: 930px; margin: 0 auto; padding: 0 1.5rem 4rem; }}

    header {{
      padding: 5rem 0 3rem; border-bottom: 1px solid var(--border); margin-bottom: 3rem;
    }}

    .header-eyebrow {{
      font-size: 11px; letter-spacing: .2em; text-transform: uppercase;
      color: var(--teal); margin-bottom: 1rem;
    }}

    h1 {{
      font-family: 'Libre Baskerville', serif; font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 700; color: var(--white); line-height: 1.1; margin-bottom: 1.25rem;
    }}
    h1 em {{ font-style: italic; color: var(--teal); }}

    .header-desc {{
      font-family: 'Libre Baskerville', serif; font-size: 1rem;
      max-width: 660px; line-height: 1.8; margin-bottom: 2rem;
    }}

    .header-meta {{
      display: flex; flex-wrap: wrap; gap: 1.5rem;
      font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--text-dim);
    }}
    .header-meta strong {{ color: var(--teal); }}

    .section-title {{
      font-family: 'Libre Baskerville', serif; font-size: .8rem; letter-spacing: .18em;
      text-transform: uppercase; color: var(--text-dim); margin-bottom: 1.5rem;
      display: flex; align-items: center; gap: 1rem;
    }}
    .section-title::after {{ content: ''; flex: 1; height: 1px; background: var(--border); }}

    .cards {{ display: flex; flex-direction: column; gap: 1.25rem; }}
    .card {{
      background: var(--bg2); border: 1px solid var(--border);
      border-left: 3px solid var(--rank-color, var(--teal));
      border-radius: 4px; display: flex; align-items: stretch;
      transition: border-color .2s, box-shadow .2s; animation: fadeUp .5s ease both;
    }}
    .card:hover {{ box-shadow: 0 0 30px rgba(58,247,181,.07); border-color: var(--rank-color, var(--teal)); }}

    @keyframes fadeUp {{
      from {{ opacity:0; transform: translateY(12px); }}
      to {{ opacity:1; transform: translateY(0); }}
    }}

    .card-rank {{
      width: 56px; min-width: 56px; display: flex; align-items: center; justify-content: center;
      font-size: 1.6rem; font-weight: 700; color: var(--border); border-right: 1px solid var(--border);
    }}

    .card-body {{ flex: 1; padding: 1.25rem 1.5rem; }}
    .card-header {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }}
    .rank-type {{ font-size: 9px; letter-spacing: .18em; text-transform: uppercase; color: var(--teal); margin-bottom: .25rem; }}
    .planet-name {{
      font-family: 'Libre Baskerville', serif; font-size: 1.3rem;
      color: var(--white); font-weight: 700; margin-bottom: .2rem;
    }}
    .planet-meta {{ font-size: 11px; color: var(--text-dim); letter-spacing: .05em; }}

    .badges {{ display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .6rem; }}
    .badge {{
      font-size: 9px; color: #f7c948; border: 1px solid #473b20;
      background: rgba(247,201,72,.06); border-radius: 999px; padding: .15rem .45rem;
      letter-spacing: .04em;
    }}

    .composite-gauge {{ text-align: center; flex-shrink: 0; }}
    .composite-gauge svg {{ display: block; }}
    .gauge-label {{
      font-size: 9px; letter-spacing: .14em; text-transform: uppercase;
      color: var(--text-dim); margin-top: .2rem;
    }}

    .score-summary {{
      display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: .9rem;
      font-size: 10px; color: var(--text-dim); letter-spacing: .08em; text-transform: uppercase;
    }}
    .score-summary strong {{ color: var(--white); }}

    .score-bars {{ display: flex; flex-direction: column; gap: .45rem; }}
    .score-row {{
      display: grid; grid-template-columns: 160px 1fr 42px;
      align-items: center; gap: .6rem;
    }}
    .score-label {{
      font-size: 10px; letter-spacing: .06em; text-transform: uppercase;
      color: var(--text-dim); white-space: nowrap;
    }}
    .bar-track {{ height: 5px; background: var(--bg3); border-radius: 3px; overflow: hidden; }}
    .bar-fill {{
      height: 100%; border-radius: 3px;
      transition: width 1s cubic-bezier(.22,1,.36,1);
      animation: growBar 1.2s cubic-bezier(.22,1,.36,1) both;
    }}
    @keyframes growBar {{ from {{ width: 0 !important; }} }}
    .score-val {{ font-size: 11px; font-weight: 600; text-align: right; }}

    .methodology {{
      margin-top: 4rem; padding-top: 2rem; border-top: 1px solid var(--border);
    }}
    .methodology h3 {{
      font-family: 'Libre Baskerville', serif; font-size: 1rem; color: var(--white); margin-bottom: 1rem;
    }}
    .methodology p {{
      font-family:'Libre Baskerville',serif; font-size:.85rem;
      color:var(--text-dim); line-height:1.8; max-width:720px; margin-bottom:1rem;
    }}
    .method-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem; margin-top: 1rem;
    }}
    .method-item {{ background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; padding: 1rem; }}
    .method-item h4 {{
      font-size: 10px; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .4rem; color: var(--teal);
    }}
    .method-item h4.magnetic {{ color: var(--amber); }}
    .method-item p {{ font-size: .8rem; margin: 0; }}

    footer {{
      margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border);
      font-size: 10px; letter-spacing: .08em; color: var(--text-dim);
      display: flex; flex-wrap: wrap; gap: 1rem; justify-content: space-between; align-items: center;
    }}
    footer a {{ color: var(--teal); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}

    @media (max-width: 650px) {{
      .card-header {{ flex-direction: column; }}
      .composite-gauge {{ align-self: flex-end; }}
      .score-row {{ grid-template-columns: 122px 1fr 36px; }}
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
        A ranked catalogue of confirmed exoplanets scored across physical
        habitability dimensions, then filtered through evidence, thermal sanity,
        and data confidence. Missing data now lowers confidence instead of
        accidentally promoting a planet.
      </p>
      <div class="header-meta">
        <span>Data source: <strong>NASA Exoplanet Archive</strong></span>
        <span>Updated: <strong>{updated}</strong></span>
        <span>Source: <strong>{esc(source)}</strong></span>
      </div>
    </header>

    <p class="section-title">Top 10 Evidence-Adjusted Candidates</p>

    <div class="cards">
      {cards_html}
    </div>

    <section class="methodology">
      <h3>Scoring Methodology</h3>
      <p>
        Vigil now uses an evidence-adjusted score. Missing dimensions count as
        missing evidence, not free points. Ultra-short-period lava worlds, gas-giant
        radii, and extreme equilibrium temperatures are capped before ranking.
      </p>
      <div class="method-grid">
        <div class="method-item">
          <h4 class="magnetic">★ Magnetic Field (25%)</h4>
          <p>Inferred from mass, density proxy, tidal-locking risk, and system age.</p>
        </div>
        <div class="method-item">
          <h4>Habitable Zone (25%)</h4>
          <p>Computed from stellar luminosity and orbital distance where available.</p>
        </div>
        <div class="method-item">
          <h4>Thermal Guardrail</h4>
          <p>Known equilibrium temperatures cap obviously roasted or frozen worlds.</p>
        </div>
        <div class="method-item">
          <h4>Rocky Surface (20%)</h4>
          <p>Uses the radius gap to penalise likely mini-Neptunes and gas-rich worlds.</p>
        </div>
        <div class="method-item">
          <h4>Data Confidence</h4>
          <p>Rewards planets with enough mass, radius, orbit, stellar and age evidence.</p>
        </div>
        <div class="method-item">
          <h4>Vigil Score</h4>
          <p>Final ranking = evidence score × confidence factor, then physical caps.</p>
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


def main():
    planets_raw, source = load_planets()
    print(f"Loaded {len(planets_raw)} planets from: {source}")
    print("Scoring...")
    html_out = generate_html(planets_raw, source)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Generated index.html ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
