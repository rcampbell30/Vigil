# Vigil Methodology

Vigil is an exoplanet habitability and SETI-targeting index. It does not claim that any planet is inhabited, Earth-like, or safe. It ranks confirmed exoplanets by available evidence, physical plausibility, data confidence, and long-term observational interest.

## Core principle

Most exoplanet rankings can be distorted by missing data. A world with unknown mass, atmosphere, temperature, or orbital context should not rise simply because hostile values are absent.

Vigil therefore uses this rule:

```text
Unknown does not count as good evidence.
```

The final ranking is not just a raw habitability score. It is an evidence-adjusted score.

```text
Vigil Score = weighted evidence score × data confidence factor, then physical caps
```

## Main scoring dimensions

| Dimension | Purpose |
|---|---|
| Magnetic field likelihood | Rewards worlds more likely to retain atmospheric shielding over long timescales. |
| Habitable zone position | Rewards orbital positions compatible with liquid-water conditions when stellar data allows. |
| Rocky surface likelihood | Rewards likely rocky/super-Earth candidates and penalises mini-Neptune/gas-giant-size bodies. |
| Thermal plausibility | Uses equilibrium temperature as a sanity check where available. |
| Stellar stability | Penalises hostile host-star context, especially flare/tidal-lock risk around small M dwarfs. |
| System age | Rewards systems old enough for stability while penalising very young systems. |
| Atmosphere retention | Uses rough physical proxies for whether an atmosphere could plausibly persist. |
| Data confidence | Penalises missing values, unresolved measurements, and under-measured candidates. |

## Guardrails

Vigil applies hard or soft caps when a planet is likely to be physically hostile even if partial scores look attractive.

Guardrails include:

- ultra-short orbital periods;
- extreme equilibrium temperatures;
- gas-giant-size or mini-Neptune-size radii;
- missing mass or radius values;
- missing habitable-zone evidence;
- low data-confidence scores;
- known M-dwarf flare or tidal-lock risk.

## Why magnetic fields are weighted heavily

A planet in the right orbit can still be a poor long-term biosignature or SETI target if stellar wind strips its atmosphere. Vigil therefore gives magnetic-field likelihood high importance as a survival filter rather than treating habitability as only “Earth-sized and in the habitable zone.”

## Current output lenses

The dashboard separates four useful categories:

1. **Current winner** — the highest NASA-baseline evidence-adjusted score.
2. **Cleanest top candidate** — the highest strong candidate without major risk flags.
3. **Closest serious target** — a nearby candidate with enough score strength to matter for follow-up.
4. **Wildcard watch** — a candidate that could move significantly if missing values or source disagreements are resolved.

This matters because the most habitable-looking world is not always the best observational target, and the best observational target is not always the most Earth-like.

## Current limitations

- The live ranking currently uses NASA Exoplanet Archive as its active baseline source.
- Other catalogues are documented as planned comparison/enrichment layers, not yet merged into the score.
- Some dimensions use proxy logic because direct measurements such as magnetic fields and atmospheres are rare.
- The model is useful for prioritisation, not proof of habitability.

## Future scoring split

A future version should separate the score into two outputs:

### Habitability Score

Measures the planet itself:

- radius;
- mass;
- likely rocky composition;
- stellar flux;
- equilibrium temperature;
- orbital position;
- eccentricity;
- host star type;
- activity/tidal-lock risk;
- system age;
- atmosphere-retention proxies.

### SETI / Observability Priority Score

Measures whether the planet is worth watching:

- distance from Earth;
- host-star brightness;
- transiting status;
- observability for JWST/ELT/HWO-style follow-up;
- signal detectability;
- known atmosphere constraints;
- publication density;
- data confidence.

This split will make Vigil stronger because a planet can be highly promising biologically but poor observationally, or less Earth-like but much more useful for follow-up.
