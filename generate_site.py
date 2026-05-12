"""
generate_site.py - Generates index.html for the Vigil exoplanet habitability site.

Reads data/latest.csv (produced by scraper.py), scores all planets using
habitability.py, and writes a self-contained static index.html for GitHub Pages.

The generated page is designed as a static observatory dashboard: no build tools,
no client-side framework, no external JavaScript.

Author: Rory
"""

import csv
import html
import os
from datetime import datetime
from habitability import top_n


SAMPLE_ROWS = [
    {"pl_name": "Kepler-442 b", "hostname": "Kepler-442", "sy_dist": "342", "pl_rade": "1.34", "pl_masse": "2.3", "pl_orbper": "112.3", "pl_orbsmax": "0.409", "pl_eqt": "233", "st_teff": "4402", "st_lum": "-0.951", "st_age": "2.9", "disc_year": "2015", "discoverymethod": "Transit", "pl_controv_flag": "0"},
    {"pl_name": "TOI-700 d", "hostname": "TOI-700", "sy_dist": "31.1", "pl_rade": "1.19", "pl_masse": "1.57", "pl_orbper": "37.4", "pl_orbsmax": "0.163", "pl_eqt": "269", "st_teff": "3480", "st_lum": "-1.633", "st_age": "1.5", "disc_year": "2020", "discoverymethod": "Transit", "pl_controv_flag": "0"},
    {"pl_name": "Proxima Cen b", "hostname": "Proxima Centauri", "sy_dist": "1.3", "pl_rade": "1.1", "pl_masse": "1.07", "pl_orbper": "11.2", "pl_orbsmax": "0.0485", "pl_eqt": "234", "st_teff": "3050", "st_lum": "-2.810", "st_age": "4.85", "disc_year": "2016", "discoverymethod": "Radial Velocity", "pl_controv_flag": "0"},
    {"pl_name": "TRAPPIST-1 e", "hostname": "TRAPPIST-1", "sy_dist": "12.1", "pl_rade": "0.92", "pl_masse": "0.69", "pl_orbper": "6.1", "pl_orbsmax": "0.0293", "pl_eqt": "251", "st_teff": "2566", "st_lum": "-3.283", "st_age": "7.6", "disc_year": "2017", "discoverymethod": "Transit", "pl_controv_flag": "0"},
    {"pl_name": "Kepler-62 f", "hostname": "Kepler-62", "sy_dist": "990", "pl_rade": "1.41", "pl_masse": "2.8", "pl_orbper": "267.3", "pl_orbsmax": "0.718", "pl_eqt": "208", "st_teff": "4925", "st_lum": "-0.677", "st_age": "7.0", "disc_year": "2013", "discoverymethod": "Transit", "pl_controv_flag": "0"},
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
        return "#334155"
    if score >= 7.5:
        return "#3af7b5"
    if score >= 5.0:
        return "#f7c948"
    return "#f75a3a"


def fmt_score(score, digits: int = 1) -> str:
    """Format a score for display."""
    return "N/A" if score is None else f"{float(score):.{digits}f}"


def fmt_distance(distance_pc) -> str:
    """Format distance in parsecs."""
    return "unknown" if distance_pc is None else f"{float(distance_pc):.1f} pc"


def split_flags(raw: str) -> list[str]:
    """Split comma-separated risk/missing strings into clean labels."""
    if not raw or raw == "none":
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def first_risk(planet: dict) -> str:
    """Return the first short risk flag for the comparison table."""
    flags = split_flags(planet.get("risk_flags", ""))
    return flags[0] if flags else "none"


def build_rank_explanation(planet: dict) -> str:
    """Build one concise explanation of why a candidate ranked where it did."""
    potential = planet.get("evidence_score")
    confidence = planet.get("data_confidence_score")
    ceiling = planet.get("habitability_ceiling")
    flags = split_flags(planet.get("risk_flags", ""))
    missing = split_flags(planet.get("missing_data", ""))

    has_m_dwarf_risk = any("M-dwarf" in flag or "tidal" in flag for flag in flags)
    has_physical_cap = ceiling is not None and ceiling < 8.0
    has_missing_core = any(
        key in ", ".join(missing)
        for key in ["magnetic_field", "habitable_zone", "atmosphere_hold", "system_age"]
    )

    if potential is not None and potential >= 7.5 and confidence is not None and confidence >= 8.0 and not flags:
        return "Strong measured potential and confidence, with no major physical cap triggered."
    if has_m_dwarf_risk and confidence is not None and confidence >= 7.0:
        return "Nearby or well measured, but capped by M-dwarf flare or tidal-lock risk."
    if has_missing_core:
        return "Promising candidate, but confidence is reduced by missing core habitability data."
    if has_physical_cap:
        return "High or moderate potential, but final rank is limited by a physical ceiling."
    if confidence is not None and confidence < 6.0:
        return "Potential remains uncertain because the archive record is not complete enough."
    return "Balanced candidate with ranking driven by measured potential, confidence, and physical caps."


def render_stat(label: str, value: str, note: str = "") -> str:
    """Render a dashboard stat tile."""
    note_html = f'<span class="stat-note">{esc(note)}</span>' if note else ""
    return f"""
      <div class="stat-card">
        <span class="stat-label">{esc(label)}</span>
        <strong>{esc(value)}</strong>
        {note_html}
      </div>"""


def render_metric(label: str, value: str, tone: str = "") -> str:
    """Render a compact metric inside a target dossier."""
    tone_class = f" metric-{tone}" if tone else ""
    return f"""
      <div class="metric{tone_class}">
        <span>{esc(label)}</span>
        <strong>{esc(value)}</strong>
      </div>"""


def render_score_bar(label: str, score, modifier: str = "") -> str:
    """Render one score bar row as HTML."""
    pct = 0 if score is None else max(0, min(100, float(score) * 10))
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


def render_score_columns(planet: dict) -> str:
    """Render score bars in two desktop columns."""
    left = (
        render_score_bar("Magnetic Field", planet.get("score_magnetic_field"), "magnetic") +
        render_score_bar("Habitable Zone", planet.get("score_habitable_zone")) +
        render_score_bar("Thermal Plausibility", planet.get("score_thermal_plausibility")) +
        render_score_bar("Rocky Surface", planet.get("score_rocky_likelihood"))
    )
    right = (
        render_score_bar("Stellar Stability", planet.get("score_stellar_stability")) +
        render_score_bar("System Age", planet.get("score_system_age")) +
        render_score_bar("Atmos. Retention", planet.get("score_atmosphere_hold")) +
        render_score_bar("Data Confidence", planet.get("data_confidence_score"))
    )
    return f"""
        <div class="score-grid">
          <div>{left}</div>
          <div>{right}</div>
        </div>"""


def render_badges(planet: dict) -> str:
    """Render risk/missing badges."""
    badges = []
    badges.extend(split_flags(planet.get("risk_flags", "")))

    missing = planet.get("missing_data", "")
    if missing and missing != "none":
        badges.append(f"missing: {missing}")

    if not badges:
        return '<div class="badges"><span class="badge badge-clear">no major flags</span></div>'

    return '<div class="badges">' + "".join(f'<span class="badge">{esc(badge)}</span>' for badge in badges[:6]) + "</div>"


def render_planet_card(rank: int, planet: dict) -> str:
    """Render one planet target dossier."""
    name = esc(planet["pl_name"])
    host = esc(planet["hostname"])
    dist_str = fmt_distance(planet.get("sy_dist_pc"))
    disc = esc(planet.get("disc_year", ""))

    vigil = planet.get("composite_score")
    vigil_str = "—" if vigil is None else f"{float(vigil):.2f}"
    vigil_color = score_color(vigil)
    vigil_pct = 0 if vigil is None else max(0, min(100, float(vigil) * 10))

    circ = 251.3
    dash_fill = circ * vigil_pct / 100

    potential = planet.get("evidence_score")
    confidence = planet.get("data_confidence_score")
    ceiling = planet.get("habitability_ceiling")
    rank_type = "ranked target" if planet.get("rankable") else "watchlist target"
    explanation = build_rank_explanation(planet)

    metrics = (
        render_metric("Potential", fmt_score(potential, 2), "potential") +
        render_metric("Confidence", fmt_score(confidence), "confidence") +
        render_metric("Physical Ceiling", fmt_score(ceiling), "ceiling") +
        render_metric("Distance", dist_str)
    )

    return f"""
  <article class="target-card" style="--rank-color:{vigil_color};">
    <div class="target-rank">
      <span>Rank</span>
      <strong>{rank:02d}</strong>
    </div>
    <div class="target-body">
      <div class="target-topline">
        <div>
          <p class="rank-type">{rank_type}</p>
          <h2 class="planet-name">{name}</h2>
          <p class="planet-meta">Host: {host} &nbsp;·&nbsp; Distance: {esc(dist_str)} &nbsp;·&nbsp; Discovery: {disc}</p>
        </div>
        <div class="vigil-gauge">
          <svg viewBox="0 0 100 100" width="104" height="104" aria-hidden="true">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#172033" stroke-width="8"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="{vigil_color}" stroke-width="8"
              stroke-dasharray="{dash_fill:.1f} {circ:.1f}"
              stroke-dashoffset="{circ * 0.25:.1f}"
              stroke-linecap="round"/>
            <text x="50" y="50" text-anchor="middle" dy="0.35em"
              font-family="'JetBrains Mono',monospace" font-size="16"
              fill="{vigil_color}" font-weight="700">{vigil_str}</text>
          </svg>
          <p>Vigil Score</p>
        </div>
      </div>

      <div class="metric-strip">{metrics}</div>
      <p class="rank-explanation">{esc(explanation)}</p>
      {render_badges(planet)}
      {render_score_columns(planet)}
    </div>
  </article>"""


def render_table(results: list[dict]) -> str:
    """Render a compact top-10 comparison table."""
    rows = []
    for idx, planet in enumerate(results, 1):
        rows.append(f"""
        <tr>
          <td>{idx:02d}</td>
          <td>{esc(planet.get('pl_name'))}</td>
          <td>{fmt_score(planet.get('composite_score'), 2)}</td>
          <td>{fmt_score(planet.get('data_confidence_score'))}</td>
          <td>{esc(fmt_distance(planet.get('sy_dist_pc')))}</td>
          <td>{esc(first_risk(planet))}</td>
        </tr>""")

    return f"""
    <section class="table-section">
      <p class="section-title">Top 10 at a glance</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Planet</th>
              <th>Vigil</th>
              <th>Confidence</th>
              <th>Distance</th>
              <th>Main risk</th>
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>"""


def render_methodology() -> str:
    """Render methodology accordions."""
    sections = [
        ("Magnetic field likelihood", "Estimated from planet mass, density proxy, tidal-locking risk, and system age. The score favours rocky worlds able to sustain a long-term dynamo."),
        ("Habitable zone score", "Computed from stellar luminosity and orbital distance when both are available. The score peaks near the middle of the conservative liquid-water zone."),
        ("Thermal guardrail", "Known equilibrium temperature is used as a sanity check. Extremely hot or cold worlds are capped even when other fields look promising."),
        ("Rocky surface likelihood", "Uses planet radius and the radius gap to penalise likely mini-Neptunes, gas-rich worlds, and giant planets."),
        ("Data confidence", "Missing values reduce confidence. Unknown does not mean good or bad; it means the final rank should be treated with less certainty."),
        ("Physical caps", "Ultra-short orbits, extreme temperatures, and oversized radii apply hard ceilings so hostile planets cannot rank as top-tier targets."),
        ("What Vigil does not claim", "Vigil does not claim these planets are inhabited. It ranks confirmed exoplanets by available evidence and physical plausibility for long-term habitability and future SETI prioritisation."),
    ]
    return "".join(
        f"""
        <details>
          <summary>{esc(title)}</summary>
          <p>{esc(body)}</p>
        </details>"""
        for title, body in sections
    )


def generate_html(planets_raw: list[dict], source: str) -> str:
    """Generate the full static site."""
    results = top_n(planets_raw, n=10)
    updated = datetime.now().strftime("%d %B %Y")
    cards_html = "".join(render_planet_card(i + 1, p) for i, p in enumerate(results))
    table_html = render_table(results)

    stats_html = "".join([
        render_stat("Confirmed planets scanned", f"{len(planets_raw):,}"),
        render_stat("Candidates displayed", f"{len(results):,}"),
        render_stat("Data source", "NASA Archive"),
        render_stat("Last refresh", updated),
        render_stat("Scoring model", "Evidence-adjusted v2"),
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Vigil — The Long Watch</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #050812;
      --panel: #0a101d;
      --panel-2: #0e1728;
      --panel-3: #111c30;
      --line: #1f314a;
      --line-soft: rgba(125, 164, 214, .14);
      --text: #c8d5e7;
      --muted: #7c8fa8;
      --dim: #52647d;
      --white: #edf5ff;
      --teal: #3af7b5;
      --cyan: #70d7ff;
      --amber: #ffb454;
      --red: #f75a3a;
      --shadow: rgba(0, 0, 0, .45);
    }}

    html {{ scroll-behavior: smooth; }}
    body {{
      background:
        radial-gradient(circle at 18% 10%, rgba(58, 247, 181, .08), transparent 24rem),
        radial-gradient(circle at 80% 0%, rgba(112, 215, 255, .06), transparent 26rem),
        linear-gradient(180deg, #050812 0%, #070b14 45%, #050812 100%);
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      line-height: 1.6;
      min-height: 100vh;
      overflow-x: hidden;
    }}

    #stars {{
      position: fixed;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      opacity: .6;
      background:
        radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 23% 67%, rgba(255,255,255,.45) 0%, transparent 100%),
        radial-gradient(1px 1px at 38% 32%, rgba(255,255,255,.6) 0%, transparent 100%),
        radial-gradient(1px 1px at 52% 80%, rgba(255,255,255,.4) 0%, transparent 100%),
        radial-gradient(1px 1px at 67% 20%, rgba(255,255,255,.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 79% 55%, rgba(255,255,255,.5) 0%, transparent 100%),
        radial-gradient(1px 1px at 88% 8%, rgba(255,255,255,.65) 0%, transparent 100%),
        radial-gradient(1px 1px at 95% 75%, rgba(255,255,255,.4) 0%, transparent 100%);
    }}

    .wrapper {{
      position: relative;
      z-index: 1;
      max-width: 1180px;
      margin: 0 auto;
      padding: 0 1.25rem 4rem;
    }}

    header {{
      padding: 4.5rem 0 2rem;
      border-bottom: 1px solid var(--line-soft);
      margin-bottom: 1.5rem;
    }}

    .eyebrow {{
      display: inline-flex;
      gap: .6rem;
      align-items: center;
      color: var(--teal);
      font-size: 11px;
      letter-spacing: .18em;
      text-transform: uppercase;
      margin-bottom: 1.2rem;
    }}

    .eyebrow::before {{
      content: '';
      width: .55rem;
      height: .55rem;
      border-radius: 50%;
      background: var(--teal);
      box-shadow: 0 0 22px rgba(58,247,181,.55);
    }}

    h1 {{
      font-family: 'Libre Baskerville', serif;
      color: var(--white);
      font-size: clamp(2.35rem, 5vw, 4.4rem);
      line-height: .98;
      margin-bottom: 1.2rem;
    }}

    h1 em {{ color: var(--teal); font-style: italic; }}

    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(280px, .8fr);
      gap: 2rem;
      align-items: end;
    }}

    .hero-copy {{
      max-width: 720px;
      font-family: 'Libre Baskerville', serif;
      font-size: 1rem;
      line-height: 1.9;
      color: var(--text);
    }}

    .system-note {{
      border: 1px solid var(--line-soft);
      background: linear-gradient(180deg, rgba(14,23,40,.9), rgba(10,16,29,.75));
      padding: 1rem;
      box-shadow: 0 18px 45px var(--shadow);
    }}

    .system-note span {{
      display: block;
      color: var(--dim);
      font-size: 10px;
      letter-spacing: .14em;
      text-transform: uppercase;
      margin-bottom: .4rem;
    }}

    .system-note strong {{ color: var(--white); font-size: .9rem; }}

    .stats {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: .75rem;
      margin: 1.5rem 0 3rem;
    }}

    .stat-card {{
      min-height: 92px;
      border: 1px solid var(--line-soft);
      background: rgba(10, 16, 29, .78);
      padding: .9rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .stat-label {{
      color: var(--dim);
      font-size: 9px;
      letter-spacing: .12em;
      text-transform: uppercase;
    }}

    .stat-card strong {{
      color: var(--white);
      font-size: clamp(1rem, 2vw, 1.35rem);
      line-height: 1.2;
    }}

    .stat-note {{ color: var(--muted); font-size: 10px; }}

    .section-title {{
      font-family: 'Libre Baskerville', serif;
      font-size: .85rem;
      letter-spacing: .18em;
      text-transform: uppercase;
      color: var(--muted);
      margin: 2.5rem 0 1.25rem;
      display: flex;
      gap: 1rem;
      align-items: center;
    }}

    .section-title::after {{ content: ''; height: 1px; flex: 1; background: var(--line-soft); }}

    .cards {{ display: grid; gap: 1rem; }}

    .target-card {{
      display: grid;
      grid-template-columns: 84px 1fr;
      border: 1px solid var(--line-soft);
      border-left: 4px solid var(--rank-color, var(--teal));
      background: linear-gradient(180deg, rgba(14,23,40,.9), rgba(8,13,24,.94));
      box-shadow: 0 18px 45px rgba(0,0,0,.25);
    }}

    .target-rank {{
      border-right: 1px solid var(--line-soft);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: .35rem;
      background: rgba(255,255,255,.015);
    }}

    .target-rank span {{
      color: var(--dim);
      font-size: 9px;
      letter-spacing: .16em;
      text-transform: uppercase;
    }}

    .target-rank strong {{
      color: var(--white);
      font-size: 1.55rem;
    }}

    .target-body {{ padding: 1.2rem; }}

    .target-topline {{
      display: flex;
      gap: 1rem;
      justify-content: space-between;
      align-items: flex-start;
    }}

    .rank-type {{
      color: var(--teal);
      font-size: 9px;
      letter-spacing: .18em;
      text-transform: uppercase;
      margin-bottom: .25rem;
    }}

    .planet-name {{
      font-family: 'Libre Baskerville', serif;
      color: var(--white);
      font-size: clamp(1.25rem, 2.3vw, 1.7rem);
      margin-bottom: .2rem;
    }}

    .planet-meta {{
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .04em;
    }}

    .vigil-gauge {{ flex-shrink: 0; text-align: center; }}
    .vigil-gauge svg {{ display: block; }}
    .vigil-gauge p {{
      color: var(--dim);
      font-size: 9px;
      letter-spacing: .14em;
      text-transform: uppercase;
      margin-top: .15rem;
    }}

    .metric-strip {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: .55rem;
      margin: 1rem 0;
    }}

    .metric {{
      border: 1px solid var(--line-soft);
      background: rgba(5,8,18,.55);
      padding: .65rem;
    }}

    .metric span {{
      display: block;
      color: var(--dim);
      font-size: 9px;
      letter-spacing: .12em;
      text-transform: uppercase;
      margin-bottom: .2rem;
    }}

    .metric strong {{ color: var(--white); font-size: .95rem; }}
    .metric-potential strong {{ color: var(--cyan); }}
    .metric-confidence strong {{ color: var(--teal); }}
    .metric-ceiling strong {{ color: var(--amber); }}

    .rank-explanation {{
      border-left: 2px solid var(--rank-color, var(--teal));
      padding-left: .8rem;
      margin: .9rem 0;
      color: var(--text);
      font-family: 'Libre Baskerville', serif;
      font-size: .88rem;
      line-height: 1.7;
    }}

    .badges {{ display: flex; flex-wrap: wrap; gap: .35rem; margin: .8rem 0 1rem; }}
    .badge {{
      color: #f7c948;
      border: 1px solid rgba(247,201,72,.28);
      background: rgba(247,201,72,.06);
      border-radius: 999px;
      padding: .18rem .5rem;
      font-size: 9px;
      letter-spacing: .04em;
    }}
    .badge-clear {{ color: var(--teal); border-color: rgba(58,247,181,.28); background: rgba(58,247,181,.06); }}

    .score-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: .8rem 1rem;
    }}

    .score-row {{
      display: grid;
      grid-template-columns: 168px 1fr 42px;
      gap: .55rem;
      align-items: center;
      margin-bottom: .45rem;
    }}

    .score-label {{
      color: var(--dim);
      font-size: 10px;
      letter-spacing: .06em;
      text-transform: uppercase;
      white-space: nowrap;
    }}

    .bar-track {{
      height: 5px;
      background: #131d30;
      border-radius: 999px;
      overflow: hidden;
    }}

    .bar-fill {{ height: 100%; border-radius: 999px; animation: growBar 1s cubic-bezier(.22,1,.36,1) both; }}
    @keyframes growBar {{ from {{ width: 0 !important; }} }}

    .score-val {{ font-size: 11px; font-weight: 700; text-align: right; }}

    .table-section {{ margin-top: 3rem; }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--line-soft);
      background: rgba(10,16,29,.72);
    }}

    table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
    th, td {{
      border-bottom: 1px solid var(--line-soft);
      padding: .75rem .8rem;
      text-align: left;
      font-size: 11px;
    }}
    th {{
      color: var(--dim);
      text-transform: uppercase;
      letter-spacing: .12em;
      background: rgba(255,255,255,.025);
    }}
    td {{ color: var(--text); }}
    tbody tr:last-child td {{ border-bottom: none; }}

    .methodology {{
      margin-top: 3.5rem;
      padding-top: 2rem;
      border-top: 1px solid var(--line-soft);
    }}

    .methodology h3 {{
      font-family: 'Libre Baskerville', serif;
      color: var(--white);
      margin-bottom: .75rem;
    }}

    details {{
      border: 1px solid var(--line-soft);
      background: rgba(10,16,29,.72);
      margin-bottom: .6rem;
      padding: .85rem 1rem;
    }}

    summary {{
      cursor: pointer;
      color: var(--teal);
      font-size: 11px;
      letter-spacing: .12em;
      text-transform: uppercase;
    }}

    details p {{
      margin-top: .7rem;
      color: var(--muted);
      font-family: 'Libre Baskerville', serif;
      line-height: 1.75;
      max-width: 780px;
    }}

    footer {{
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--line-soft);
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 1rem;
      color: var(--dim);
      font-size: 10px;
      letter-spacing: .08em;
    }}

    footer a {{ color: var(--teal); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}

    @media (max-width: 900px) {{
      .hero-grid, .stats, .metric-strip, .score-grid {{ grid-template-columns: 1fr; }}
      .target-card {{ grid-template-columns: 56px 1fr; }}
      .target-rank strong {{ font-size: 1.1rem; }}
      .target-topline {{ flex-direction: column; }}
      .vigil-gauge {{ align-self: flex-end; }}
      .score-row {{ grid-template-columns: 142px 1fr 38px; }}
    }}

    @media (max-width: 560px) {{
      .wrapper {{ padding-inline: .85rem; }}
      header {{ padding-top: 3rem; }}
      .target-card {{ grid-template-columns: 1fr; }}
      .target-rank {{ flex-direction: row; justify-content: flex-start; padding: .55rem .8rem; border-right: none; border-bottom: 1px solid var(--line-soft); }}
      .score-row {{ grid-template-columns: 1fr 1fr 36px; }}
      .score-label {{ font-size: 9px; }}
    }}
  </style>
</head>
<body>
  <div id="stars"></div>
  <div class="wrapper">
    <header>
      <p class="eyebrow">Exoplanet Habitability Index / SETI Targeting</p>
      <div class="hero-grid">
        <div>
          <h1>Vigil —<br/><em>The Long Watch.</em></h1>
          <p class="hero-copy">
            Vigil ranks confirmed exoplanets by evidence-adjusted habitability.
            Unknown values reduce confidence. Hostile physics caps the score.
            Nearby, well-measured, survivable worlds rise.
          </p>
        </div>
        <div class="system-note">
          <span>Current source</span>
          <strong>{esc(source)}</strong>
        </div>
      </div>
    </header>

    <section class="stats" aria-label="Dashboard summary">
      {stats_html}
    </section>

    <p class="section-title">Top 10 evidence-adjusted target dossiers</p>

    <div class="cards">
      {cards_html}
    </div>

    {table_html}

    <section class="methodology">
      <h3>Methodology</h3>
      {render_methodology()}
    </section>

    <footer>
      <span>Data: <a href="https://exoplanetarchive.ipac.caltech.edu" target="_blank">NASA Exoplanet Archive</a></span>
      <span>Model: Evidence-adjusted v2</span>
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
