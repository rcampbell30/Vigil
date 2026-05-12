"""
habitability.py - Scores confirmed exoplanets across key habitability dimensions.

Each planet gets a score between 0 and 10 for six physical dimensions, plus a
weighted composite score.  The composite is what the website will use to rank
the top candidates for SETI technosignature searches.

WHY THESE SIX DIMENSIONS?
  Magnetic field  - Without one, stellar wind strips the atmosphere over
                    geological timescales (this killed Mars).  Arguably the
                    most underrated filter in habitability discussions.
  Habitable zone  - Liquid water requires the right orbital distance relative
                    to stellar luminosity.  More reliable than equilibrium
                    temperature alone since NASA often leaves that field blank.
  Rocky likelihood- The radius gap at ~1.5 Re separates rocky worlds from
                    mini-Neptunes with thick H/He envelopes.  Life as we know
                    it needs a solid/liquid surface.
  Stellar stability- M dwarfs flare violently and tidally lock their planets.
                    F stars burn out too fast.  G/K stars are the sweet spot.
  System age      - Complex life took ~4 Gyr on Earth.  Young systems haven't
                    had time; very old cores may have cooled and gone geologically
                    dead.
  Atmosphere hold - Escape velocity proxy.  Too low a surface gravity and the
                    planet bleeds its atmosphere to space over time.

MISSING DATA:
  NASA's archive has gaps - many planets lack mass, age, or luminosity values.
  Each scorer returns None when it can't score rather than guessing.  The
  composite skips None dimensions and notes what is missing.

Author: Rory
"""

import math
import csv
from typing import Optional


# ---------------------------------------------------------------------------
# Constants used in scoring calculations
# ---------------------------------------------------------------------------

# Earth's physical properties - used as reference values throughout.
EARTH_RADIUS_RE   = 1.0    # Earth radii (by definition)
EARTH_MASS_ME     = 1.0    # Earth masses (by definition)
EARTH_TEMP_K      = 255.0  # Earth's equilibrium temperature in Kelvin

# The "radius gap" (Fulton gap) - above this, planets are likely mini-Neptunes
# with thick hydrogen/helium envelopes rather than rocky surfaces.
RADIUS_GAP_RE = 1.5

# Habitable zone inner and outer edge coefficients from Kopparapu et al. 2013.
# These are used to compute the HZ boundaries from stellar luminosity.
# Inner edge (runaway greenhouse): flux = 1.107 solar
# Outer edge (maximum greenhouse): flux = 0.356 solar
HZ_INNER_FLUX = 1.107   # Solar flux units at inner HZ edge
HZ_OUTER_FLUX = 0.356   # Solar flux units at outer HZ edge

# Stellar temperature thresholds for spectral type classification (in Kelvin).
# Used to score stellar stability.
STAR_TYPE_BOUNDS = {
    "O": (30000, float("inf")),   # Very hot, very short-lived - terrible for life
    "B": (10000, 30000),           # Hot, short-lived - poor
    "A": (7500, 10000),            # Too much UV, short-lived - poor
    "F": (6000, 7500),             # Warm, decent but shorter lifespan than G
    "G": (5200, 6000),             # Sun-like - excellent
    "K": (3700, 5200),             # Slightly cooler, long-lived - excellent
    "M": (2400, 3700),             # Red dwarfs - flares, tidal locking risk
}

# Tidal locking threshold: planets with orbital periods shorter than this
# around M-dwarf stars are likely tidally locked (one face always toward star).
# Estimated from empirical models; ~20 days is a commonly used threshold.
TIDAL_LOCK_PERIOD_DAYS = 20.0

# Composite score weights.  Must sum to 1.0.
# Magnetic field and HZ position get extra weight - they're binary filters
# in practice (no field = atmosphere gone, wrong zone = no liquid water).
WEIGHTS = {
    "magnetic_field":    0.25,   # Most underappreciated filter
    "habitable_zone":    0.25,   # Classic filter
    "rocky_likelihood":  0.20,   # Surface needed for life as we know it
    "stellar_stability": 0.15,   # Long-term stable radiation environment
    "system_age":        0.10,   # Time for evolution
    "atmosphere_hold":   0.05,   # Escape velocity proxy - correlated with mass
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _safe_float(value: str) -> Optional[float]:
    """Convert a string to float, returning None if blank or unparseable.

    NASA's CSV files use empty strings for missing values.  We return None
    so callers can explicitly handle the missing-data case.

    :param value: String value from the CSV, possibly blank.
    :return: Float value, or None if conversion fails.
    """
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    """Clamp a value to the range [low, high].

    Used throughout to prevent scores drifting outside 0-10 due to extreme
    planet parameters.

    :param value: The value to clamp.
    :param low:   Lower bound (default 0).
    :param high:  Upper bound (default 10).
    :return: Value clamped to [low, high].
    """
    return max(low, min(high, value))


def _gaussian(x: float, centre: float, width: float) -> float:
    """Return a Gaussian (bell curve) value between 0 and 1.

    Used to build smooth scoring curves that peak at an ideal value and
    fall off on either side, rather than harsh step functions.

    :param x:      The input value to score.
    :param centre: The ideal value (peak of the bell curve).
    :param width:  Controls how quickly the score falls away from the peak.
    :return: A value between 0 and 1, peaking at 1 when x == centre.
    """
    # Standard Gaussian formula: e^(-(x - centre)^2 / (2 * width^2))
    return math.exp(-((x - centre) ** 2) / (2 * width ** 2))


# ---------------------------------------------------------------------------
# Individual dimension scorers
# Each returns a float 0-10, or None if data is insufficient.
# ---------------------------------------------------------------------------

def score_magnetic_field(
    mass_me: Optional[float],
    radius_re: Optional[float],
    orbital_period_days: Optional[float],
    star_teff_k: Optional[float],
    system_age_gyr: Optional[float],
) -> Optional[float]:
    """Score the likelihood of a planetary magnetic field, 0-10.

    We cannot directly detect exoplanet magnetic fields yet (some tentative
    radio detections exist but none confirmed).  Instead we score based on
    physical proxies that determine whether a dynamo is plausible:

    MASS COMPONENT
      A dynamo requires a liquid iron core undergoing convection.  Too small
      (like Mars at 0.1 Me) and the core solidifies quickly.  Too large and
      the planet is likely a gas giant with a different kind of field.
      Optimal range: ~0.5 to 5 Earth masses for a rocky dynamo.

    DENSITY PROXY
      If both mass and radius are available we compute bulk density.  A density
      close to Earth's (5.5 g/cm3) suggests a rocky, iron-rich interior.  Low
      density suggests a gas/water world where a dynamo works differently.

    TIDAL LOCKING PENALTY
      Planets in short orbits around cool M-dwarf stars are likely tidally
      locked (same face always toward the star, like our Moon to Earth).
      A tidally locked planet rotates very slowly, which weakens the dynamo.
      We apply a penalty for planets that are probably tidally locked.

    AGE COMPONENT
      Very young cores haven't fully differentiated; very old cores may have
      cooled and solidified.  Earth's core is ~4.5 Gyr old and still liquid.

    :param mass_me:             Planet mass in Earth masses, or None.
    :param radius_re:           Planet radius in Earth radii, or None.
    :param orbital_period_days: Orbital period in days, or None.
    :param star_teff_k:         Host star effective temperature in K, or None.
    :param system_age_gyr:      System age in gigayears, or None.
    :return: Score 0-10, or None if mass is missing (mass is essential here).
    """
    # Mass is fundamental to dynamo physics - can't score without it
    if mass_me is None:
        return None

    # --- Mass component (0 to 8 points) ---
    # Bell curve centred at 2 Me - slightly super-Earth is optimal for a
    # large liquid iron core.  Width of 2 lets G/K planets still score well.
    mass_score = _gaussian(mass_me, centre=2.0, width=2.0) * 8.0

    # Steep penalty for gas giants (above ~8 Me likely a mini-Neptune or bigger)
    # These still have magnetic fields but not rocky dynamos
    if mass_me > 8.0:
        mass_score = _clamp(mass_score * (8.0 / mass_me), 0, 4)

    # Very small planets (Mars-like) have no active dynamo
    if mass_me < 0.2:
        mass_score = mass_score * (mass_me / 0.2)

    # --- Density proxy (0 to 1 bonus point) ---
    density_bonus = 0.0
    if mass_me is not None and radius_re is not None and radius_re > 0:
        # Density in g/cm3: mass (in grams) / volume (in cm3)
        # Earth mass = 5.972e27 g, Earth radius = 6.371e8 cm
        mass_g      = mass_me * 5.972e27
        radius_cm   = radius_re * 6.371e8
        volume_cm3  = (4 / 3) * math.pi * radius_cm ** 3
        density     = mass_g / volume_cm3
        # Earth's density is ~5.5 g/cm3.  Score peaks there, penalises low density.
        density_bonus = _gaussian(density, centre=5.5, width=2.0) * 1.0

    # --- Tidal locking penalty (subtract 0 to 3 points) ---
    tidal_penalty = 0.0
    if orbital_period_days is not None and star_teff_k is not None:
        # Only M-dwarf stars are cool enough for their HZ to overlap the tidal
        # locking zone.  Stars hotter than ~4000K have HZ planets far enough
        # out to avoid locking.
        is_m_dwarf = star_teff_k < 4000
        is_short_period = orbital_period_days < TIDAL_LOCK_PERIOD_DAYS
        if is_m_dwarf and is_short_period:
            # Scale penalty: very short periods get full -3, longer periods less
            ratio = orbital_period_days / TIDAL_LOCK_PERIOD_DAYS
            tidal_penalty = (1 - ratio) * 3.0

    # --- Age component (0 to 1 bonus point) ---
    age_bonus = 0.0
    if system_age_gyr is not None:
        # Ideal age 2-8 Gyr: core still liquid, life had enough time
        age_bonus = _gaussian(system_age_gyr, centre=4.5, width=3.0) * 1.0

    # --- Combine all components ---
    raw_score = mass_score + density_bonus + age_bonus - tidal_penalty
    return _clamp(raw_score)


def score_habitable_zone(
    luminosity_log_solar: Optional[float],
    semi_major_axis_au: Optional[float],
) -> Optional[float]:
    """Score how well the planet's orbit sits within the habitable zone, 0-10.

    Uses the Kopparapu et al. 2013 HZ model, which defines the zone by the
    stellar flux the planet receives relative to Earth.  The inner edge is
    the runaway greenhouse limit (Venus-like heating); the outer edge is the
    maximum greenhouse limit (CO2 freezing out).

    We compute a smooth score that peaks at the centre of the HZ and falls
    off toward the edges, rather than a binary in/out flag.

    :param luminosity_log_solar: Stellar luminosity in log10(solar units), or None.
    :param semi_major_axis_au:   Planet's semi-major axis in AU, or None.
    :return: Score 0-10, or None if either parameter is missing.
    """
    if luminosity_log_solar is None or semi_major_axis_au is None:
        return None
    if semi_major_axis_au <= 0:
        return None

    # Convert log luminosity back to linear solar units
    luminosity_solar = 10 ** luminosity_log_solar

    # Flux received by the planet in solar flux units (Earth receives 1.0)
    # Follows inverse square law: flux = L / d^2
    flux_received = luminosity_solar / (semi_major_axis_au ** 2)

    # The habitable zone is where flux is between the outer and inner edges.
    # We compute the fraction through the HZ from outer to inner.
    hz_range = HZ_INNER_FLUX - HZ_OUTER_FLUX   # Total flux width of HZ

    if hz_range <= 0:
        return None

    # Position within the HZ: 0.0 = outer edge, 1.0 = inner edge
    hz_position = (flux_received - HZ_OUTER_FLUX) / hz_range

    # Score peaks at the middle of the HZ (hz_position = 0.5)
    # Bell curve with width 0.35 gives full marks at centre, ~5/10 at edges
    hz_score = _gaussian(hz_position, centre=0.5, width=0.35) * 10.0

    # Planets outside the HZ entirely get a rapidly decaying score
    if flux_received > HZ_INNER_FLUX:
        # Too hot - Venus zone
        overshoot = (flux_received - HZ_INNER_FLUX) / HZ_INNER_FLUX
        hz_score = _clamp(5.0 * math.exp(-overshoot * 3))
    elif flux_received < HZ_OUTER_FLUX:
        # Too cold - beyond snowline
        undershoot = (HZ_OUTER_FLUX - flux_received) / HZ_OUTER_FLUX
        hz_score = _clamp(5.0 * math.exp(-undershoot * 3))

    return _clamp(hz_score)


def score_rocky_likelihood(radius_re: Optional[float]) -> Optional[float]:
    """Score the likelihood that the planet has a rocky surface, 0-10.

    The Fulton et al. 2017 radius gap (also called the photoevaporation gap)
    shows a bimodal distribution of planet radii with a gap around 1.5-1.7 Re.
    Below this gap, planets are typically rocky (super-Earths); above it they
    tend to be mini-Neptunes with thick H/He envelopes - unlikely to have
    a solid surface accessible for life as we know it.

    :param radius_re: Planet radius in Earth radii, or None.
    :return: Score 0-10, or None if radius is missing.
    """
    if radius_re is None:
        return None

    if radius_re <= 0:
        return None

    # Scoring bands based on the radius gap:
    if radius_re < 0.5:
        # Very small - Mercury-like, probably airless
        score = _gaussian(radius_re, centre=0.5, width=0.2) * 8.0

    elif radius_re <= 1.2:
        # Ideal rocky range - Earth-like or slightly smaller
        score = _gaussian(radius_re, centre=1.0, width=0.3) * 10.0

    elif radius_re <= RADIUS_GAP_RE:
        # Upper rocky range - probably still rocky but transitional
        score = _gaussian(radius_re, centre=1.0, width=0.5) * 10.0

    elif radius_re <= 2.5:
        # Mini-Neptune territory - thick atmosphere, no surface likely
        score = 3.0 * (2.5 - radius_re) / (2.5 - RADIUS_GAP_RE)

    else:
        # Neptune/gas giant - score rapidly drops to near zero
        score = max(0.0, 1.5 - (radius_re - 2.5) * 0.5)

    return _clamp(score)


def score_stellar_stability(star_teff_k: Optional[float]) -> Optional[float]:
    """Score how stable and habitable-friendly the host star is, 0-10.

    Life needs billions of years of stable radiation.  Stars too hot burn out
    quickly and bathe planets in UV.  M dwarfs are long-lived but frequently
    flare, potentially stripping atmospheres, and their HZ is close enough
    that tidal locking is common.  G and K dwarfs are the sweet spot.

    :param star_teff_k: Stellar effective temperature in Kelvin, or None.
    :return: Score 0-10, or None if temperature is missing.
    """
    if star_teff_k is None:
        return None

    # Score lookup table approach: each spectral band maps to a score range.
    # We use smooth transitions so there are no sudden jumps at boundaries.

    if star_teff_k >= 30000:
        # O stars: incredibly luminous, live only millions of years, extreme UV
        return 0.5

    elif star_teff_k >= 10000:
        # B stars: very hot, short-lived, too much UV
        return _clamp(1.0 + (star_teff_k - 10000) / 20000)

    elif star_teff_k >= 7500:
        # A stars: warm, UV-heavy, shorter lifespan (~2 Gyr)
        t = (star_teff_k - 7500) / (10000 - 7500)   # 0=A-cool, 1=A-hot
        return _clamp(2.0 + t * 1.0)

    elif star_teff_k >= 6000:
        # F stars: slightly hotter than sun, decent but elevated UV
        t = (star_teff_k - 6000) / (7500 - 6000)    # 0=F-cool, 1=F-hot
        return _clamp(6.5 - t * 3.5)

    elif star_teff_k >= 5200:
        # G stars: sun-like, stable, long-lived - excellent
        t = (star_teff_k - 5200) / (6000 - 5200)    # 0=G-cool, 1=G-hot
        return _clamp(8.5 + t * 1.0)

    elif star_teff_k >= 3700:
        # K stars: slightly cooler than sun, very long-lived, low UV - ideal
        # Many astrobiologists consider K dwarfs the best habitable zone hosts
        t = (star_teff_k - 3700) / (5200 - 3700)    # 0=K-cool, 1=K-hot
        return _clamp(8.0 + t * 1.5)

    else:
        # M dwarfs: very long-lived but active flare stars; HZ is tidally
        # locked zone; significant atmospheric stripping risk.
        # Cooler M dwarfs are worse (more flare-active)
        t = max(0, (star_teff_k - 2400) / (3700 - 2400))  # 0=coolest, 1=3700K
        return _clamp(3.0 + t * 2.5)


def score_system_age(age_gyr: Optional[float]) -> Optional[float]:
    """Score the system age for habitability, 0-10.

    Earth took ~4 Gyr to produce complex multicellular life.  Systems younger
    than ~1 Gyr haven't had enough time.  Very old systems (>10 Gyr) may have
    geologically dead planets with cold, solid cores and no volcanism to recycle
    nutrients.  The sweet spot is 4-8 Gyr.

    :param age_gyr: System age in gigayears, or None.
    :return: Score 0-10, or None if age is missing.
    """
    if age_gyr is None:
        return None

    if age_gyr < 0:
        return None

    if age_gyr < 0.5:
        # Too young - system may still be forming; heavy bombardment ongoing
        return _clamp(age_gyr * 2.0)   # Linear ramp from 0 at 0 Gyr to 1 at 0.5 Gyr

    elif age_gyr < 1.0:
        # Still young but settling down
        return _clamp(1.0 + (age_gyr - 0.5) * 6.0)

    else:
        # Gaussian centred at 5 Gyr (roughly Earth's age), wide width of 4 Gyr
        # so that anything from 2-9 Gyr still scores well
        return _clamp(_gaussian(age_gyr, centre=5.0, width=4.0) * 10.0)


def score_atmosphere_hold(
    mass_me: Optional[float],
    radius_re: Optional[float],
) -> Optional[float]:
    """Score the planet's ability to retain an atmosphere, 0-10.

    Surface gravity and escape velocity both depend on mass and radius.  A
    higher escape velocity means the planet can hold onto lighter atmospheric
    gases (including water vapour and nitrogen) against stellar wind stripping.

    Earth's escape velocity is 11.2 km/s.  Mars's is only 5.0 km/s and it has
    lost most of its atmosphere over geological time.

    We use escape velocity as the proxy since it directly determines what
    molecules the planet can hold.  Score peaks at Earth-like values.

    :param mass_me:   Planet mass in Earth masses, or None.
    :param radius_re: Planet radius in Earth radii, or None.
    :return: Score 0-10, or None if either parameter is missing.
    """
    if mass_me is None or radius_re is None:
        return None
    if radius_re <= 0:
        return None

    # Escape velocity scales as sqrt(mass / radius) in relative Earth units.
    # Earth's escape velocity = 11.2 km/s (normalised to 1.0 here).
    v_esc_relative = math.sqrt(mass_me / radius_re)

    # Score peaks at Earth-like escape velocity (1.0).
    # Too low = atmosphere lost to space.  Too high = likely gas giant, or
    # atmosphere retained but possibly too heavy (H2 dominated).
    if v_esc_relative < 0.4:
        # Mars-like: very likely to lose atmosphere over Gyr timescales
        score = _gaussian(v_esc_relative, centre=0.5, width=0.2) * 5.0

    elif v_esc_relative <= 1.5:
        # Earth-like to slightly super-Earth - ideal range
        score = _gaussian(v_esc_relative, centre=1.0, width=0.4) * 10.0

    elif v_esc_relative <= 3.0:
        # Strong gravity - good retention but may be mini-Neptune
        score = _clamp(8.0 - (v_esc_relative - 1.5) * 2.0)

    else:
        # Very high escape velocity - almost certainly a gas giant
        score = _clamp(3.0 - (v_esc_relative - 3.0))

    return _clamp(score)


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

def score_planet(row: dict) -> dict:
    """Score all habitability dimensions for a single planet row from the CSV.

    Extracts the relevant fields, calls each dimension scorer, and computes
    the weighted composite.  Dimensions with missing data are excluded from
    the composite (their weight is redistributed proportionally).

    :param row: A dict representing one planet row from the NASA CSV.
    :return: A new dict containing all scores and the composite, plus the
             original planet name and host star for reference.
    """
    # Extract raw values, converting empty strings to None
    mass_me        = _safe_float(row.get("pl_masse"))
    radius_re      = _safe_float(row.get("pl_rade"))
    period_days    = _safe_float(row.get("pl_orbper"))
    sma_au         = _safe_float(row.get("pl_orbsmax"))
    star_teff      = _safe_float(row.get("st_teff"))
    star_lum_log   = _safe_float(row.get("st_lum"))
    age_gyr        = _safe_float(row.get("st_age"))

    # Call each dimension scorer
    scores = {
        "magnetic_field":    score_magnetic_field(mass_me, radius_re, period_days, star_teff, age_gyr),
        "habitable_zone":    score_habitable_zone(star_lum_log, sma_au),
        "rocky_likelihood":  score_rocky_likelihood(radius_re),
        "stellar_stability": score_stellar_stability(star_teff),
        "system_age":        score_system_age(age_gyr),
        "atmosphere_hold":   score_atmosphere_hold(mass_me, radius_re),
    }

    # Compute weighted composite, skipping dimensions that returned None.
    # We redistribute the weight of missing dimensions among available ones.
    available = {k: v for k, v in scores.items() if v is not None}
    missing   = {k for k, v in scores.items() if v is None}

    if available:
        # Sum up the weights of available dimensions
        total_weight = sum(WEIGHTS[k] for k in available)
        # Weighted average: sum(score * weight) / total_weight
        composite = sum(scores[k] * WEIGHTS[k] for k in available) / total_weight
    else:
        # No dimensions could be scored - happens for very poorly characterised planets
        composite = None

    return {
        "pl_name":         row.get("pl_name", "Unknown"),
        "hostname":        row.get("hostname", "Unknown"),
        "sy_dist_pc":      _safe_float(row.get("sy_dist")),
        "disc_year":       row.get("disc_year", ""),
        # Raw physical values for display
        "mass_me":         mass_me,
        "radius_re":       radius_re,
        "period_days":     period_days,
        "sma_au":          sma_au,
        "star_teff_k":     star_teff,
        "age_gyr":         age_gyr,
        # Individual dimension scores
        "score_magnetic_field":    scores["magnetic_field"],
        "score_habitable_zone":    scores["habitable_zone"],
        "score_rocky_likelihood":  scores["rocky_likelihood"],
        "score_stellar_stability": scores["stellar_stability"],
        "score_system_age":        scores["system_age"],
        "score_atmosphere_hold":   scores["atmosphere_hold"],
        # Composite
        "composite_score": round(composite, 3) if composite is not None else None,
        # Transparency: tell users which dimensions had to be skipped
        "missing_data":    ", ".join(sorted(missing)) if missing else "none",
    }


def score_all(planets: list[dict]) -> list[dict]:
    """Score every planet in a list and return results sorted by composite score.

    Planets with no composite score (all dimensions missing) are placed at the
    end of the list.

    :param planets: List of planet dicts as returned by the scraper.
    :return: Sorted list of scored planet dicts, best first.
    """
    scored = [score_planet(p) for p in planets]

    # Sort: planets with a composite score come first (descending), then
    # unscored planets at the end.
    scored.sort(
        key=lambda p: p["composite_score"] if p["composite_score"] is not None else -1,
        reverse=True
    )
    return scored


def top_n(planets: list[dict], n: int = 10) -> list[dict]:
    """Return the top N planets by composite habitability score.

    :param planets: List of planet dicts from the scraper.
    :param n:       Number of top candidates to return.  Defaults to 10.
    :return: Top N scored planet dicts.
    """
    all_scored = score_all(planets)
    # Filter to only planets that actually have a composite score
    with_scores = [p for p in all_scored if p["composite_score"] is not None]
    return with_scores[:n]


# ---------------------------------------------------------------------------
# Quick demo when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Load the latest scraped data and score it
    import os

    latest_path = os.path.join("data", "latest.csv")

    if not os.path.exists(latest_path):
        print("No data found. Run scraper.py first to download planet data.")
    else:
        with open(latest_path, newline="", encoding="utf-8") as f:
            planets = list(csv.DictReader(f))

        print(f"Loaded {len(planets):,} planets. Scoring...")
        results = top_n(planets, n=10)

        print("\n=== TOP 10 HABITABLE CANDIDATES ===\n")
        for i, p in enumerate(results, 1):
            print(f"{i:>2}. {p['pl_name']:<30} composite={p['composite_score']:.2f}/10")
            print(f"      Host: {p['hostname']:<20}  dist={p['sy_dist_pc']} pc  "
                  f"disc={p['disc_year']}")
            print(f"      Mag field : {p['score_magnetic_field']}/10  "
                  f"HZ pos    : {p['score_habitable_zone']}/10")
            print(f"      Rocky     : {p['score_rocky_likelihood']}/10  "
                  f"Star stab : {p['score_stellar_stability']}/10")
            print(f"      Age       : {p['score_system_age']}/10  "
                  f"Atm hold  : {p['score_atmosphere_hold']}/10")
            if p['missing_data'] != 'none':
                print(f"      (missing data: {p['missing_data']})")
            print()
