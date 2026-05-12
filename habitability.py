"""
habitability.py - Scores confirmed exoplanets across key habitability dimensions.

Each planet gets a 0-10 score across physical habitability dimensions, then a
final evidence-adjusted score used by the Vigil website.

IMPORTANT SCORING RULE:
  Missing data must never make a planet look better. A planet can only score
  highly if it has enough evidence behind the ranking. Missing dimensions are
  counted as zero contribution to the evidence score, then the result is
  down-weighted by a data-confidence score.

WHY THESE DIMENSIONS?
  Magnetic field     - Without one, stellar wind can strip the atmosphere over
                       geological timescales.
  Habitable zone     - Liquid water requires the right orbital distance relative
                       to stellar luminosity.
  Rocky likelihood   - The radius gap at ~1.5 Re separates rocky worlds from
                       mini-Neptunes.
  Stellar stability  - G/K stars are generally better long-term hosts than
                       flare-heavy M dwarfs or short-lived hot stars.
  System age         - Complex life took ~4 Gyr on Earth.
  Atmosphere hold    - Escape velocity affects long-term atmosphere retention.

GUARDRAILS:
  Vigil also applies sanity checks for ultra-short orbits, excessive equilibrium
  temperatures, suspiciously large radii, and low data confidence. These caps
  stop hot close-in planets with missing data from floating to the top.

Author: Rory
"""

import math
import csv
from typing import Optional


# ---------------------------------------------------------------------------
# Constants used in scoring calculations
# ---------------------------------------------------------------------------

EARTH_RADIUS_RE = 1.0
EARTH_MASS_ME = 1.0
EARTH_TEMP_K = 255.0

# Above this, many planets are mini-Neptunes rather than rocky worlds.
RADIUS_GAP_RE = 1.5

# Kopparapu et al. 2013 conservative habitable-zone flux edges.
HZ_INNER_FLUX = 1.107
HZ_OUTER_FLUX = 0.356

# M-dwarf close-orbit planets below this period are treated as high tidal-lock risk.
TIDAL_LOCK_PERIOD_DAYS = 20.0

# Core scientific score weights. These sum to 1.0.
WEIGHTS = {
    "magnetic_field": 0.25,
    "habitable_zone": 0.25,
    "rocky_likelihood": 0.20,
    "stellar_stability": 0.15,
    "system_age": 0.10,
    "atmosphere_hold": 0.05,
}

# Confidence weights. These also sum to 1.0.
# The orbit/temperature term is deliberately heavy because a planet cannot be a
# top habitability candidate if we do not know whether it is roasted or frozen.
CONFIDENCE_WEIGHTS = {
    "radius": 0.18,
    "mass": 0.18,
    "period": 0.10,
    "orbit_or_temperature": 0.22,
    "star_teff": 0.12,
    "star_luminosity": 0.08,
    "system_age": 0.08,
    "distance": 0.04,
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _safe_float(value) -> Optional[float]:
    """Convert a value to float, returning None if blank or unparseable."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    """Clamp a value to the range [low, high]."""
    return max(low, min(high, value))


def _gaussian(x: float, centre: float, width: float) -> float:
    """Return a Gaussian value between 0 and 1."""
    return math.exp(-((x - centre) ** 2) / (2 * width ** 2))


def _round_score(value: Optional[float]) -> Optional[float]:
    """Round a score for output while preserving None."""
    return round(value, 3) if value is not None else None


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
    """Score the likelihood of a rocky-planet magnetic dynamo, 0-10."""
    if mass_me is None:
        return None

    # Slightly super-Earth mass is favourable for a large liquid iron core.
    mass_score = _gaussian(mass_me, centre=2.0, width=2.0) * 8.0

    # Gas giants can have magnetic fields, but not the rocky-world shield we want.
    if mass_me > 8.0:
        mass_score = _clamp(mass_score * (8.0 / mass_me), 0, 4)

    # Mars-like bodies cool too fast.
    if mass_me < 0.2:
        mass_score *= mass_me / 0.2

    density_bonus = 0.0
    if radius_re is not None and radius_re > 0:
        mass_g = mass_me * 5.972e27
        radius_cm = radius_re * 6.371e8
        volume_cm3 = (4 / 3) * math.pi * radius_cm ** 3
        density = mass_g / volume_cm3
        density_bonus = _gaussian(density, centre=5.5, width=2.0) * 1.0

    tidal_penalty = 0.0
    if orbital_period_days is not None and star_teff_k is not None:
        is_m_dwarf = star_teff_k < 4000
        is_short_period = orbital_period_days < TIDAL_LOCK_PERIOD_DAYS
        if is_m_dwarf and is_short_period:
            ratio = orbital_period_days / TIDAL_LOCK_PERIOD_DAYS
            tidal_penalty = (1 - ratio) * 3.0

    age_bonus = 0.0
    if system_age_gyr is not None:
        age_bonus = _gaussian(system_age_gyr, centre=4.5, width=3.0) * 1.0

    return _clamp(mass_score + density_bonus + age_bonus - tidal_penalty)


def score_habitable_zone(
    luminosity_log_solar: Optional[float],
    semi_major_axis_au: Optional[float],
) -> Optional[float]:
    """Score how well the orbit sits inside the stellar habitable zone, 0-10."""
    if luminosity_log_solar is None or semi_major_axis_au is None:
        return None
    if semi_major_axis_au <= 0:
        return None

    luminosity_solar = 10 ** luminosity_log_solar
    flux_received = luminosity_solar / (semi_major_axis_au ** 2)
    hz_range = HZ_INNER_FLUX - HZ_OUTER_FLUX

    if hz_range <= 0:
        return None

    hz_position = (flux_received - HZ_OUTER_FLUX) / hz_range
    hz_score = _gaussian(hz_position, centre=0.5, width=0.35) * 10.0

    if flux_received > HZ_INNER_FLUX:
        overshoot = (flux_received - HZ_INNER_FLUX) / HZ_INNER_FLUX
        hz_score = _clamp(5.0 * math.exp(-overshoot * 3))
    elif flux_received < HZ_OUTER_FLUX:
        undershoot = (HZ_OUTER_FLUX - flux_received) / HZ_OUTER_FLUX
        hz_score = _clamp(5.0 * math.exp(-undershoot * 3))

    return _clamp(hz_score)


def score_thermal_plausibility(equilibrium_temp_k: Optional[float]) -> Optional[float]:
    """Score whether the listed equilibrium temperature is life-plausible.

    This is a guardrail rather than a core weighted dimension. It helps catch
    worlds where habitable-zone fields are missing but the temperature is clearly
    too hot or too cold.
    """
    if equilibrium_temp_k is None:
        return None
    if equilibrium_temp_k <= 0:
        return None

    # Earth equilibrium temperature is ~255 K. Keep the curve broad because
    # greenhouse effects and albedo are unknown.
    score = _gaussian(equilibrium_temp_k, centre=270.0, width=85.0) * 10.0

    if equilibrium_temp_k > 373:
        # Above the boiling point of water at 1 atm: sharply less plausible.
        score *= math.exp(-(equilibrium_temp_k - 373) / 120)
    if equilibrium_temp_k > 500:
        score = min(score, 1.5)
    if equilibrium_temp_k < 150:
        score *= max(0.1, equilibrium_temp_k / 150)

    return _clamp(score)


def score_rocky_likelihood(radius_re: Optional[float]) -> Optional[float]:
    """Score the likelihood that the planet has a rocky surface, 0-10."""
    if radius_re is None or radius_re <= 0:
        return None

    if radius_re < 0.5:
        score = _gaussian(radius_re, centre=0.5, width=0.2) * 8.0
    elif radius_re <= 1.2:
        score = _gaussian(radius_re, centre=1.0, width=0.3) * 10.0
    elif radius_re <= RADIUS_GAP_RE:
        score = _gaussian(radius_re, centre=1.0, width=0.5) * 10.0
    elif radius_re <= 2.5:
        score = 3.0 * (2.5 - radius_re) / (2.5 - RADIUS_GAP_RE)
    else:
        score = max(0.0, 1.5 - (radius_re - 2.5) * 0.5)

    return _clamp(score)


def score_stellar_stability(star_teff_k: Optional[float]) -> Optional[float]:
    """Score how stable and habitable-friendly the host star is, 0-10."""
    if star_teff_k is None:
        return None

    if star_teff_k >= 30000:
        return 0.5
    if star_teff_k >= 10000:
        return _clamp(1.0 + (star_teff_k - 10000) / 20000)
    if star_teff_k >= 7500:
        t = (star_teff_k - 7500) / (10000 - 7500)
        return _clamp(2.0 + t * 1.0)
    if star_teff_k >= 6000:
        t = (star_teff_k - 6000) / (7500 - 6000)
        return _clamp(6.5 - t * 3.5)
    if star_teff_k >= 5200:
        t = (star_teff_k - 5200) / (6000 - 5200)
        return _clamp(8.5 + t * 1.0)
    if star_teff_k >= 3700:
        t = (star_teff_k - 3700) / (5200 - 3700)
        return _clamp(8.0 + t * 1.5)

    t = max(0, (star_teff_k - 2400) / (3700 - 2400))
    return _clamp(3.0 + t * 2.5)


def score_system_age(age_gyr: Optional[float]) -> Optional[float]:
    """Score the system age for habitability, 0-10."""
    if age_gyr is None or age_gyr < 0:
        return None

    if age_gyr < 0.5:
        return _clamp(age_gyr * 2.0)
    if age_gyr < 1.0:
        return _clamp(1.0 + (age_gyr - 0.5) * 6.0)

    return _clamp(_gaussian(age_gyr, centre=5.0, width=4.0) * 10.0)


def score_atmosphere_hold(
    mass_me: Optional[float],
    radius_re: Optional[float],
) -> Optional[float]:
    """Score the planet's ability to retain an atmosphere, 0-10."""
    if mass_me is None or radius_re is None or radius_re <= 0:
        return None

    v_esc_relative = math.sqrt(mass_me / radius_re)

    if v_esc_relative < 0.4:
        score = _gaussian(v_esc_relative, centre=0.5, width=0.2) * 5.0
    elif v_esc_relative <= 1.5:
        score = _gaussian(v_esc_relative, centre=1.0, width=0.4) * 10.0
    elif v_esc_relative <= 3.0:
        score = _clamp(8.0 - (v_esc_relative - 1.5) * 2.0)
    else:
        score = _clamp(3.0 - (v_esc_relative - 3.0))

    return _clamp(score)


# ---------------------------------------------------------------------------
# Evidence/confidence guardrails
# ---------------------------------------------------------------------------

def score_data_confidence(
    mass_me: Optional[float],
    radius_re: Optional[float],
    period_days: Optional[float],
    sma_au: Optional[float],
    eq_temp_k: Optional[float],
    star_teff_k: Optional[float],
    star_lum_log: Optional[float],
    system_age_gyr: Optional[float],
    distance_pc: Optional[float],
) -> float:
    """Score how much evidence exists behind the habitability estimate, 0-10."""
    confidence = 0.0

    if radius_re is not None:
        confidence += CONFIDENCE_WEIGHTS["radius"]
    if mass_me is not None:
        confidence += CONFIDENCE_WEIGHTS["mass"]
    if period_days is not None:
        confidence += CONFIDENCE_WEIGHTS["period"]

    # Best case: we can compute stellar flux. Second best: equilibrium temp.
    if sma_au is not None and star_lum_log is not None:
        confidence += CONFIDENCE_WEIGHTS["orbit_or_temperature"]
    elif eq_temp_k is not None:
        confidence += CONFIDENCE_WEIGHTS["orbit_or_temperature"] * 0.75
    elif sma_au is not None or star_lum_log is not None:
        confidence += CONFIDENCE_WEIGHTS["orbit_or_temperature"] * 0.35

    if star_teff_k is not None:
        confidence += CONFIDENCE_WEIGHTS["star_teff"]
    if star_lum_log is not None:
        confidence += CONFIDENCE_WEIGHTS["star_luminosity"]
    if system_age_gyr is not None:
        confidence += CONFIDENCE_WEIGHTS["system_age"]
    if distance_pc is not None:
        confidence += CONFIDENCE_WEIGHTS["distance"]

    return _clamp(confidence * 10.0)


def habitability_ceiling(
    radius_re: Optional[float],
    period_days: Optional[float],
    sma_au: Optional[float],
    eq_temp_k: Optional[float],
    star_teff_k: Optional[float],
) -> tuple[float, list[str]]:
    """Return the maximum allowed score and the flags causing the cap."""
    ceiling = 10.0
    flags: list[str] = []

    if period_days is not None:
        if period_days < 1.0:
            ceiling = min(ceiling, 1.5)
            flags.append("ultra-short orbit")
        elif period_days < 2.0:
            ceiling = min(ceiling, 2.5)
            flags.append("very short orbit")
        elif period_days < 5.0 and (star_teff_k is None or star_teff_k > 4500):
            ceiling = min(ceiling, 4.0)
            flags.append("hot short-period orbit")

    if eq_temp_k is not None:
        if eq_temp_k > 500:
            ceiling = min(ceiling, 1.5)
            flags.append("extreme equilibrium temperature")
        elif eq_temp_k > 373:
            ceiling = min(ceiling, 3.0)
            flags.append("too hot for stable surface water")
        elif eq_temp_k > 330:
            ceiling = min(ceiling, 6.5)
            flags.append("warm edge temperature")
        elif eq_temp_k < 100:
            ceiling = min(ceiling, 2.5)
            flags.append("extreme cold equilibrium temperature")
        elif eq_temp_k < 150:
            ceiling = min(ceiling, 5.0)
            flags.append("cold edge temperature")

    if sma_au is not None and star_teff_k is not None:
        if sma_au < 0.03 and star_teff_k > 4000:
            ceiling = min(ceiling, 2.0)
            flags.append("close-in around warm star")
        elif sma_au < 0.05 and star_teff_k > 5200:
            ceiling = min(ceiling, 3.0)
            flags.append("very close to Sun-like star")

    if radius_re is not None:
        if radius_re > 4.0:
            ceiling = min(ceiling, 2.0)
            flags.append("gas-giant-size radius")
        elif radius_re > 2.5:
            ceiling = min(ceiling, 4.0)
            flags.append("likely mini-Neptune or gas-rich world")

    return ceiling, flags


def build_risk_flags(
    scores: dict,
    confidence_score: float,
    ceiling_flags: list[str],
    mass_me: Optional[float],
    radius_re: Optional[float],
    star_teff_k: Optional[float],
) -> list[str]:
    """Build short human-readable flags for the card and debug output."""
    flags = list(ceiling_flags)

    if confidence_score < 5.0:
        flags.append("low data confidence")
    elif confidence_score < 7.0:
        flags.append("medium data confidence")

    if scores.get("habitable_zone") is None:
        flags.append("habitable-zone data missing")
    if mass_me is None:
        flags.append("mass missing")
    if radius_re is None:
        flags.append("radius missing")
    if star_teff_k is not None and star_teff_k < 3700:
        flags.append("M-dwarf flare/tidal-lock risk")

    # Deduplicate while preserving order.
    seen = set()
    unique = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            unique.append(flag)
    return unique


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

def score_planet(row: dict) -> dict:
    """Score all habitability dimensions for a single planet row from the CSV."""
    mass_me = _safe_float(row.get("pl_masse"))
    radius_re = _safe_float(row.get("pl_rade"))
    period_days = _safe_float(row.get("pl_orbper"))
    sma_au = _safe_float(row.get("pl_orbsmax"))
    eq_temp_k = _safe_float(row.get("pl_eqt"))
    star_teff = _safe_float(row.get("st_teff"))
    star_lum_log = _safe_float(row.get("st_lum"))
    age_gyr = _safe_float(row.get("st_age"))
    distance_pc = _safe_float(row.get("sy_dist"))

    scores = {
        "magnetic_field": score_magnetic_field(mass_me, radius_re, period_days, star_teff, age_gyr),
        "habitable_zone": score_habitable_zone(star_lum_log, sma_au),
        "rocky_likelihood": score_rocky_likelihood(radius_re),
        "stellar_stability": score_stellar_stability(star_teff),
        "system_age": score_system_age(age_gyr),
        "atmosphere_hold": score_atmosphere_hold(mass_me, radius_re),
    }

    thermal_plausibility = score_thermal_plausibility(eq_temp_k)

    available = {k: v for k, v in scores.items() if v is not None}
    missing = {k for k, v in scores.items() if v is None}

    if available:
        # Evidence score treats missing dimensions as zero contribution. This is
        # deliberate: lack of evidence should never inflate a planet into the top 10.
        evidence_score = sum(
            (scores[k] if scores[k] is not None else 0.0) * WEIGHTS[k]
            for k in WEIGHTS
        )

        # Useful for debugging only: what the score would have been if we ignored
        # missing dimensions and redistributed their weights.
        available_weight = sum(WEIGHTS[k] for k in available)
        available_only_score = sum(scores[k] * WEIGHTS[k] for k in available) / available_weight
    else:
        evidence_score = None
        available_only_score = None

    confidence_score = score_data_confidence(
        mass_me,
        radius_re,
        period_days,
        sma_au,
        eq_temp_k,
        star_teff,
        star_lum_log,
        age_gyr,
        distance_pc,
    )

    ceiling, ceiling_flags = habitability_ceiling(
        radius_re,
        period_days,
        sma_au,
        eq_temp_k,
        star_teff,
    )

    if evidence_score is None:
        final_score = None
    else:
        # Confidence factor is square-rooted so incomplete-but-useful planets are
        # not buried completely, but low-evidence planets cannot hit the top.
        confidence_factor = math.sqrt(confidence_score / 10.0) if confidence_score > 0 else 0.0
        final_score = evidence_score * confidence_factor

        # If equilibrium temperature is known, make it a soft guardrail too.
        if thermal_plausibility is not None and thermal_plausibility < 4.0:
            final_score *= max(0.2, thermal_plausibility / 4.0)

        # Hard physical sanity cap for lava worlds, giant planets, etc.
        final_score = min(final_score, ceiling)

    risk_flags = build_risk_flags(
        scores,
        confidence_score,
        ceiling_flags,
        mass_me,
        radius_re,
        star_teff,
    )

    rankable = (
        final_score is not None
        and confidence_score >= 4.0
        and ceiling >= 5.0
        and (
            scores["habitable_zone"] is not None
            or (thermal_plausibility is not None and thermal_plausibility >= 4.0)
        )
    )

    return {
        "pl_name": row.get("pl_name", "Unknown"),
        "hostname": row.get("hostname", "Unknown"),
        "sy_dist_pc": distance_pc,
        "disc_year": row.get("disc_year", ""),
        # Raw physical values for display/debug
        "mass_me": mass_me,
        "radius_re": radius_re,
        "period_days": period_days,
        "sma_au": sma_au,
        "eq_temp_k": eq_temp_k,
        "star_teff_k": star_teff,
        "age_gyr": age_gyr,
        # Individual dimension scores
        "score_magnetic_field": _round_score(scores["magnetic_field"]),
        "score_habitable_zone": _round_score(scores["habitable_zone"]),
        "score_rocky_likelihood": _round_score(scores["rocky_likelihood"]),
        "score_stellar_stability": _round_score(scores["stellar_stability"]),
        "score_system_age": _round_score(scores["system_age"]),
        "score_atmosphere_hold": _round_score(scores["atmosphere_hold"]),
        "score_thermal_plausibility": _round_score(thermal_plausibility),
        # Evidence and confidence
        "raw_available_score": _round_score(available_only_score),
        "evidence_score": _round_score(evidence_score),
        "data_confidence_score": _round_score(confidence_score),
        "habitability_ceiling": _round_score(ceiling),
        # This is the number used by the site ranking.
        "composite_score": _round_score(final_score),
        "rankable": rankable,
        "risk_flags": ", ".join(risk_flags) if risk_flags else "none",
        "missing_data": ", ".join(sorted(missing)) if missing else "none",
    }


def score_all(planets: list[dict]) -> list[dict]:
    """Score every planet and return results sorted by final Vigil score."""
    scored = [score_planet(p) for p in planets]
    scored.sort(
        key=lambda p: p["composite_score"] if p["composite_score"] is not None else -1,
        reverse=True,
    )
    return scored


def top_n(planets: list[dict], n: int = 10) -> list[dict]:
    """Return the top N rankable planets by final Vigil score."""
    all_scored = score_all(planets)

    # The public top 10 should not include obvious lava worlds, gas giants, or
    # entries that only scored well because too much data was missing.
    rankable = [
        p for p in all_scored
        if p["composite_score"] is not None and p.get("rankable")
    ]

    if len(rankable) >= n:
        return rankable[:n]

    # Fallback: if the archive becomes sparse, still return the best-scored rows.
    fallback = [
        p for p in all_scored
        if p["composite_score"] is not None and p not in rankable
    ]
    return (rankable + fallback)[:n]


# ---------------------------------------------------------------------------
# Quick demo when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    latest_path = os.path.join("data", "latest.csv")

    if not os.path.exists(latest_path):
        print("No data found. Run scraper.py first to download planet data.")
    else:
        with open(latest_path, newline="", encoding="utf-8") as f:
            planets = list(csv.DictReader(f))

        print(f"Loaded {len(planets):,} planets. Scoring...")
        results = top_n(planets, n=10)

        print("\n=== TOP 10 VIGIL CANDIDATES ===\n")
        for i, p in enumerate(results, 1):
            print(
                f"{i:>2}. {p['pl_name']:<30} "
                f"vigil={p['composite_score']:.2f}/10 "
                f"evidence={p['evidence_score']:.2f}/10 "
                f"confidence={p['data_confidence_score']:.1f}/10"
            )
            print(
                f"      Host: {p['hostname']:<20}  "
                f"dist={p['sy_dist_pc']} pc  disc={p['disc_year']}"
            )
            print(
                f"      Mag field : {p['score_magnetic_field']}/10  "
                f"HZ pos    : {p['score_habitable_zone']}/10  "
                f"Thermal   : {p['score_thermal_plausibility']}/10"
            )
            print(
                f"      Rocky     : {p['score_rocky_likelihood']}/10  "
                f"Star stab : {p['score_stellar_stability']}/10"
            )
            print(
                f"      Age       : {p['score_system_age']}/10  "
                f"Atm hold  : {p['score_atmosphere_hold']}/10  "
                f"Ceiling   : {p['habitability_ceiling']}/10"
            )
            if p["missing_data"] != "none":
                print(f"      missing: {p['missing_data']}")
            if p["risk_flags"] != "none":
                print(f"      flags  : {p['risk_flags']}")
            print()
