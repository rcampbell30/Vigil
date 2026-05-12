# Vigil — The Long Watch

**Vigil** is a static exoplanet habitability index and SETI-targeting dashboard.

It ranks confirmed exoplanets across six physical habitability dimensions, with extra emphasis on an often underweighted filter: whether a planet is likely to keep a protective magnetic field and atmosphere over geological time.

The generated site is a dark, starfield-style catalogue showing the current top candidates, their composite scores, and their individual score bars.

## What it does

Vigil:

- Fetches confirmed exoplanet data from the NASA Exoplanet Archive
- Scores each planet across six habitability dimensions
- Ranks the strongest candidates by weighted composite score
- Generates a self-contained `index.html` suitable for GitHub Pages or any static host
- Falls back to built-in sample data if the full NASA scrape has not been run yet

## Scoring model

Each planet receives a 0–10 score across these dimensions:

| Dimension | Weight | Why it matters |
|---|---:|---|
| Magnetic field likelihood | 25% | A planet without a strong protective field can lose its atmosphere to stellar wind over geological time. |
| Habitable zone position | 25% | Liquid water requires the right stellar flux and orbital distance. |
| Rocky surface likelihood | 20% | Life as we know it needs a solid or liquid surface, not a mini-Neptune envelope. |
| Stellar stability | 15% | Stable, long-lived stars are better candidates than short-lived or flare-heavy stars. |
| System age | 10% | Complex life took billions of years on Earth, so very young systems are less promising. |
| Atmosphere retention | 5% | Escape velocity affects whether a planet can hold onto an atmosphere. |

Missing data is handled transparently. If a planet lacks a required value for one dimension, that dimension is skipped and the available weights are redistributed instead of inventing a score.

## Project files

```text
Vigil/
├── index.html          # Generated static website
├── scraper.py          # Downloads confirmed planet data from NASA
├── habitability.py     # Scores planets across the six dimensions
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

## Example workflow

```bash
git clone https://github.com/rcampbell30/Vigil.git
cd Vigil
python scraper.py
python generate_site.py
```

Then open `index.html` locally or publish the repo through GitHub Pages.

## Current site copy

The live page presents Vigil as:

> A ranked catalogue of confirmed exoplanets scored across six physical habitability dimensions — including magnetic field likelihood, the most underappreciated filter in the search for life.

## Why magnetic fields matter

Most habitability rankings focus heavily on distance from the star and surface temperature. Vigil gives magnetic-field likelihood equal importance to habitable-zone position because a world in the right orbit can still be sterile if stellar wind strips its atmosphere.

That makes the project less of a generic “Earth similarity” list and more of a long-term survivability filter for future SETI and biosignature targets.

## Data source

Planet data comes from the NASA Exoplanet Archive, using the `pscomppars` table from its TAP service.

NASA Exoplanet Archive: https://exoplanetarchive.ipac.caltech.edu/

## Status

Early but functional.

The repo already contains the core scraper, scoring model, and site generator. The current `index.html` can be served immediately, while `scraper.py` and `generate_site.py` can regenerate it from fresh NASA data.

## Next improvements

- Add a GitHub Actions workflow to refresh the NASA data yearly
- Remove duplicate `- Copy.py` files once the clean versions are confirmed
- Add a proper `requirements.txt` if external dependencies are introduced later
- Add tests for the scoring functions
- Add a methodology page explaining each scoring formula in more detail
- Add CSV export of the ranked results
- Add filters by distance, star type, discovery method, and missing-data quality

## License

MIT License.
