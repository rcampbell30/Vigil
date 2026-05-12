# Vigil — The Long Watch

**Vigil** is an exoplanet habitability index and SETI-targeting dashboard.

It ranks confirmed exoplanets using physical habitability scores, evidence weighting, data-confidence checks, and hard guardrails for obvious false positives such as lava worlds, ultra-short-period planets, gas-giant-size bodies, and poorly measured candidates.

The project now supports two output paths:

1. A self-contained generated `index.html` from the Python site generator.
2. An Astro/Tailwind frontend for Netlify or any Node-capable static host.

## What it does

Vigil:

- Fetches confirmed exoplanet data from the NASA Exoplanet Archive.
- Scores each planet across core habitability dimensions.
- Penalises missing data instead of letting it inflate the rank.
- Caps obviously uninhabitable worlds using orbital period, radius, and equilibrium-temperature guardrails.
- Ranks the strongest evidence-adjusted candidates by final Vigil score.
- Exports ranked candidates as JSON and CSV.
- Generates a static `index.html` for simple hosting.
- Builds an Astro dashboard for Netlify-style deployment.
- Falls back to built-in sample data if the full NASA scrape has not been run yet.

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

Vigil applies sanity checks for:

- Ultra-short orbital periods.
- Extreme equilibrium temperatures.
- Gas-giant-size or mini-Neptune-size radii.
- Low data confidence.
- Missing habitable-zone evidence.
- Missing mass or radius data.

These guardrails were added after the first full NASA scrape exposed a failure case: a very hot, close-in planet could rank too highly if several hostile or unknown dimensions were skipped.

## Project files

```text
Vigil/
├── index.html                    # Generated standalone static website
├── scraper.py                    # Downloads confirmed planet data from NASA
├── habitability.py               # Scores planets and applies evidence/guardrail logic
├── generate_site.py              # Builds standalone index.html
├── generate_data.py              # Exports JSON and CSV data for Astro/static use
├── data/
│   ├── latest.csv                # Latest NASA scrape
│   └── ranked_candidates.csv     # Generated ranked CSV export
├── public/data/                  # Astro-readable generated JSON/CSV exports
├── src/                          # Astro frontend
├── tests/                        # Pytest scoring/guardrail tests
├── .github/workflows/            # Refresh/test/build automation
├── package.json                  # Astro/Tailwind scripts and dependencies
├── requirements.txt              # Python test dependency list
├── netlify.toml                  # Netlify build config
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

### 2. Generate the standalone HTML site

```bash
python generate_site.py
```

This reads `data/latest.csv`, scores the planets using `habitability.py`, and writes a fresh `index.html`.

If `data/latest.csv` does not exist, the generator uses built-in sample data so the site still renders from a fresh clone.

### 3. Generate JSON and CSV exports

```bash
python generate_data.py
```

This writes:

```text
public/data/ranked_candidates.json
public/data/top_10.json
public/data/site_meta.json
public/data/ranked_candidates.csv
data/ranked_candidates.csv
```

### 4. Run the Astro frontend locally

```bash
npm install
npm run dev
```

`npm run dev` runs `python generate_data.py` first so the Astro page has data available.

### 5. Build for Netlify

```bash
npm run build
```

The Netlify config uses the same command and publishes `dist/`.

## Tests

Install the Python test dependency:

```bash
python -m pip install -r requirements.txt
```

Run the scoring/guardrail test suite:

```bash
python -m pytest
```

Current tests cover:

- Ultra-short-period score caps.
- Gas-giant-size radius caps.
- Missing-data confidence penalties.
- Temperate Earth-like candidates outranking hot close-in worlds.

## GitHub Actions

The refresh workflow can be triggered manually from the Actions tab and is also scheduled to run once a year.

It runs:

```bash
python -m pytest
python scraper.py
python generate_site.py
python generate_data.py
npm install
npm run build
```

Then it commits refreshed generated data and `index.html` if they changed.

## Deployment

Simple deployment options:

- Serve `index.html` directly with GitHub Pages or any static host.
- Use Netlify with the included `netlify.toml` for the Astro dashboard.
- Use any Node-capable static host that can run `npm run build` and publish `dist/`.

## Why magnetic fields matter

Most habitability rankings focus heavily on distance from the star and surface temperature. Vigil gives magnetic-field likelihood equal importance to habitable-zone position because a world in the right orbit can still be sterile if stellar wind strips its atmosphere.

That makes the project less of a generic Earth-similarity list and more of a long-term survivability filter for future SETI and biosignature targets.

## Data source

Planet data comes from the NASA Exoplanet Archive, using the `pscomppars` table from its TAP service.

NASA Exoplanet Archive: https://exoplanetarchive.ipac.caltech.edu/

## Status

Functional but early.

The core scraper, scoring model, evidence-adjusted ranking logic, static HTML generator, Astro data export, and basic test coverage are now in place. The current next step is polishing the Astro UI and expanding methodology documentation.

## Next improvements

- Add richer Astro filters by distance, star type, discovery method, and confidence level.
- Add a separate methodology page explaining each scoring formula.
- Add separate Habitability Score and SETI Priority Score.
- Add Earth Transit Zone and observability bonuses.
- Add downloadable CSV link in the frontend.
- Add more regression tests around known exoplanet edge cases.

## License

MIT License. See `LICENSE`.
