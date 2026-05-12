# Vigil — The Long Watch

**Vigil** is a static exoplanet habitability index and SETI-targeting dashboard.

It ranks confirmed exoplanets using physical habitability scores, evidence weighting, data-confidence checks, and hard guardrails for obvious false positives such as lava worlds, ultra-short-period planets, gas-giant-size bodies, and poorly measured candidates.

The generated site is a dark, starfield-style catalogue showing the current top candidates, their Vigil scores, confidence, risk flags, and individual score bars.

## What it does

Vigil:

- Fetches confirmed exoplanet data from the NASA Exoplanet Archive
- Scores each planet across core habitability dimensions
- Penalises missing data instead of letting it inflate the rank
- Caps obviously uninhabitable worlds using orbital period, radius, and equilibrium temperature guardrails
- Ranks the strongest evidence-adjusted candidates by final Vigil score
- Generates a self-contained `index.html` suitable for GitHub Pages or any static host
- Falls back to built-in sample data if the full NASA scrape has not been run yet

## Scoring model

Each planet receives a 0–10 score across these dimensions:

| Dimension | Weight |
|---|---:|
| Magnetic field likelihood | 25% |
| Habitable zone position | 25% |
| Rocky surface likelihood | 20% |
| Stellar stability | 15% |
| System age | 10% |
| Atmosphere retention | 5% |

The public ranking uses more than the raw dimension score.

```text
Vigil Score = evidence score × data confidence factor, then physical caps
```

This means a planet with missing mass, orbit, atmosphere-retention, or habitable-zone data cannot float to the top just because the model skipped difficult fields.

## Guardrails

Vigil now applies extra sanity checks for:

- Ultra-short orbital periods
- Extreme equilibrium temperatures
- Gas-giant-size or mini-Neptune-size radii
- Low data confidence
- Missing habitable-zone evidence
- Missing mass or radius data

These guardrails were added after the first full NASA scrape exposed a failure case: a very hot, close-in planet could rank too highly if several hostile or unknown dimensions were skipped.

## Project files

```text
Vigil/
├── index.html          # Generated static website
├── scraper.py          # Downloads confirmed planet data from NASA
├── habitability.py     # Scores planets and applies evidence/guardrail logic
├── generate_site.py    # Builds index.html from scraped or sample data
├── data/               # Created when scraper.py is run
└── README.md
```

## How it works

### 1. Scrape NASA data

```bash
python scraper.py
```

This downloads confirmed exoplanet data from the NASA Exoplanet Archive TAP service and saves:

```text
data/exoplanets_YYYY-MM-DD.csv
data/latest.csv
```

### 2. Generate the site

```bash
python generate_site.py
```

This reads `data/latest.csv`, scores the planets using `habitability.py`, and writes a fresh `index.html`.

If `data/latest.csv` does not exist, the generator uses built-in sample data so the site still renders from a fresh clone.

### 3. Deploy

Because the output is a plain static HTML file, it can be deployed with:

- GitHub Pages
- Netlify
- Vercel
- Cloudflare Pages
- Any static web host

## GitHub Actions

The repo includes a workflow that can refresh Vigil automatically.

It runs:

```bash
python scraper.py
python generate_site.py
```

The workflow can be triggered manually from the Actions tab and is also scheduled to run once a year.

## Example local workflow

```bash
git clone https://github.com/rcampbell30/Vigil.git
cd Vigil
python scraper.py
python generate_site.py
```

Then open `index.html` locally or publish the repo through GitHub Pages.

## Why magnetic fields matter

Most habitability rankings focus heavily on distance from the star and surface temperature. Vigil gives magnetic-field likelihood equal importance to habitable-zone position because a world in the right orbit can still be sterile if stellar wind strips its atmosphere.

That makes the project less of a generic “Earth similarity” list and more of a long-term survivability filter for future SETI and biosignature targets.

## Data source

Planet data comes from the NASA Exoplanet Archive, using the `pscomppars` table from its TAP service.

NASA Exoplanet Archive: https://exoplanetarchive.ipac.caltech.edu/

## Status

Early but functional.

The repo contains the core scraper, scoring model, evidence-adjusted ranking logic, and static site generator. The current `index.html` can be served immediately, while `scraper.py` and `generate_site.py` can regenerate it from fresh NASA data.

## Next improvements

- Add tests for the scoring and guardrail functions
- Add a detailed methodology page explaining each scoring formula
- Add CSV export of the ranked results
- Add filters by distance, star type, discovery method, and confidence level
- Add separate Habitability Score and SETI Priority Score
- Add Earth Transit Zone and observability bonuses later

## License

MIT License.
