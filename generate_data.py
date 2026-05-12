"""
generate_data.py - Exports scored exoplanet data as machine-readable files.

Loads data/latest.csv (produced by scraper.py), scores all planets using
habitability.py, and exports:
- public/data/ranked_candidates.json (top scored planets for Astro)
- public/data/top_10.json (top 10 for quick page rendering)
- public/data/site_meta.json (source/date/model metadata)
- data/ranked_candidates.csv (portable ranked export)
- public/data/ranked_candidates.csv (web-accessible CSV export)

Falls back to sample data if latest.csv is not found.

Author: Rory
"""

import csv
import json
import os
from datetime import datetime
from habitability import score_all, top_n


SAMPLE_ROWS = [
    {"pl_name": "Kepler-442 b", "hostname": "Kepler-442", "sy_dist": "342", "pl_rade": "1.34", "pl_masse": "2.3", "pl_orbper": "112.3", "pl_orbsmax": "0.409", "pl_eqt": "233", "st_teff": "4402", "st_lum": "-0.951", "st_age": "2.9", "disc_year": "2015", "discoverymethod": "Transit", "pl_controv_flag": "0"},
    {"pl_name": "TOI-700 d", "hostname": "TOI-700", "sy_dist": "31.1", "pl_rade": "1.19", "pl_masse": "1.57", "pl_orbper": "37.4", "pl_orbsmax": "0.163", "pl_eqt": "269", "st_teff": "3480", "st_lum": "-1.633", "st_age": "1.5", "disc_year": "2020", "discoverymethod": "Transit", "pl_controv_flag": "0"},
    {"pl_name": "Proxima Cen b", "hostname": "Proxima Centauri", "sy_dist": "1.3", "pl_rade": "1.1", "pl_masse": "1.07", "pl_orbper": "11.2", "pl_orbsmax": "0.0485", "pl_eqt": "234", "st_teff": "3050", "st_lum": "-2.810", "st_age": "4.85", "disc_year": "2016", "discoverymethod": "Radial Velocity", "pl_controv_flag": "0"},
    {"pl_name": "TRAPPIST-1 e", "hostname": "TRAPPIST-1", "sy_dist": "12.1", "pl_rade": "0.92", "pl_masse": "0.69", "pl_orbper": "6.1", "pl_orbsmax": "0.0293", "pl_eqt": "251", "st_teff": "2566", "st_lum": "-3.283", "st_age": "7.6", "disc_year": "2017", "discoverymethod": "Transit", "pl_controv_flag": "0"},
    {"pl_name": "Kepler-62 f", "hostname": "Kepler-62", "sy_dist": "990", "pl_rade": "1.41", "pl_masse": "2.8", "pl_orbper": "267.3", "pl_orbsmax": "0.718", "pl_eqt": "208", "st_teff": "4925", "st_lum": "-0.677", "st_age": "7.0", "disc_year": "2013", "discoverymethod": "Transit", "pl_controv_flag": "0"},
]

CSV_FIELDS = [
    "rank",
    "pl_name",
    "hostname",
    "composite_score",
    "evidence_score",
    "data_confidence_score",
    "habitability_ceiling",
    "sy_dist_pc",
    "mass_me",
    "radius_re",
    "period_days",
    "sma_au",
    "eq_temp_k",
    "star_teff_k",
    "age_gyr",
    "rankable",
    "risk_flags",
    "missing_data",
]


def load_planets() -> tuple[list[dict], str]:
    """Load scraped NASA data if present, otherwise use sample data."""
    latest_path = os.path.join("data", "latest.csv")

    if os.path.exists(latest_path):
        with open(latest_path, newline="", encoding="utf-8") as f:
            planets = list(csv.DictReader(f))
        return planets, f"NASA Exoplanet Archive — {len(planets):,} confirmed planets"

    print("  No data/latest.csv found - using built-in sample data.")
    return SAMPLE_ROWS, "Sample data (run scraper.py to load the full NASA archive)"


def split_labels(raw: str) -> list[str]:
    """Split a comma-separated label string."""
    if not raw or raw == "none":
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def build_rank_explanation(planet: dict) -> str:
    """Build one concise explanation of why a candidate ranked where it did."""
    potential = planet.get("evidence_score")
    confidence = planet.get("data_confidence_score")
    ceiling = planet.get("habitability_ceiling")
    flags = split_labels(planet.get("risk_flags", ""))
    missing = split_labels(planet.get("missing_data", ""))

    has_m_dwarf_risk = any("M-dwarf" in flag or "tidal" in flag for flag in flags)
    has_physical_cap = ceiling is not None and float(ceiling) < 8.0
    has_missing_core = any(
        key in " ".join(missing)
        for key in ["magnetic_field", "habitable_zone", "atmosphere_hold", "system_age"]
    )

    if potential is not None and float(potential) >= 7.5 and confidence is not None and float(confidence) >= 8.0 and not flags:
        return "Strong measured potential and confidence, with no major physical cap triggered."
    if has_m_dwarf_risk and confidence is not None and float(confidence) >= 7.0:
        return "Nearby or well measured, but capped by M-dwarf flare or tidal-lock risk."
    if has_missing_core:
        return "Promising candidate, but confidence is reduced by missing core habitability data."
    if has_physical_cap:
        return "High or moderate potential, but final rank is limited by a physical ceiling."
    if confidence is not None and float(confidence) < 6.0:
        return "Potential remains uncertain because the archive record is not complete enough."
    return "Balanced candidate with ranking driven by measured potential, confidence, and physical caps."


def maybe_float(value):
    """Return a float for JSON output, preserving None."""
    return float(value) if value is not None else None


def serialize_planet(planet: dict) -> dict:
    """Convert a scored planet dict to JSON-serializable format."""
    return {
        "pl_name": planet.get("pl_name", "Unknown"),
        "hostname": planet.get("hostname", "Unknown"),
        "sy_dist_pc": maybe_float(planet.get("sy_dist_pc")),
        "disc_year": planet.get("disc_year", ""),
        "mass_me": maybe_float(planet.get("mass_me")),
        "radius_re": maybe_float(planet.get("radius_re")),
        "period_days": maybe_float(planet.get("period_days")),
        "sma_au": maybe_float(planet.get("sma_au")),
        "eq_temp_k": maybe_float(planet.get("eq_temp_k")),
        "star_teff_k": maybe_float(planet.get("star_teff_k")),
        "age_gyr": maybe_float(planet.get("age_gyr")),
        "score_magnetic_field": maybe_float(planet.get("score_magnetic_field")),
        "score_habitable_zone": maybe_float(planet.get("score_habitable_zone")),
        "score_rocky_likelihood": maybe_float(planet.get("score_rocky_likelihood")),
        "score_stellar_stability": maybe_float(planet.get("score_stellar_stability")),
        "score_system_age": maybe_float(planet.get("score_system_age")),
        "score_atmosphere_hold": maybe_float(planet.get("score_atmosphere_hold")),
        "score_thermal_plausibility": maybe_float(planet.get("score_thermal_plausibility")),
        "evidence_score": maybe_float(planet.get("evidence_score")),
        "data_confidence_score": maybe_float(planet.get("data_confidence_score")),
        "habitability_ceiling": maybe_float(planet.get("habitability_ceiling")),
        "composite_score": maybe_float(planet.get("composite_score")),
        "rankable": bool(planet.get("rankable", False)),
        "risk_flags": planet.get("risk_flags", "none"),
        "missing_data": planet.get("missing_data", "none"),
        "rank_explanation": build_rank_explanation(planet),
    }


def ensure_output_dirs():
    """Create output directories if they do not exist."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("public/data", exist_ok=True)


def export_json(filepath: str, data: dict | list) -> None:
    """Export data as JSON with stable formatting."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"  Exported {filepath}")


def csv_row(rank: int, planet: dict) -> dict:
    """Build one row for ranked CSV export."""
    serialized = serialize_planet(planet)
    return {
        "rank": rank,
        "pl_name": serialized["pl_name"],
        "hostname": serialized["hostname"],
        "composite_score": serialized["composite_score"],
        "evidence_score": serialized["evidence_score"],
        "data_confidence_score": serialized["data_confidence_score"],
        "habitability_ceiling": serialized["habitability_ceiling"],
        "sy_dist_pc": serialized["sy_dist_pc"],
        "mass_me": serialized["mass_me"],
        "radius_re": serialized["radius_re"],
        "period_days": serialized["period_days"],
        "sma_au": serialized["sma_au"],
        "eq_temp_k": serialized["eq_temp_k"],
        "star_teff_k": serialized["star_teff_k"],
        "age_gyr": serialized["age_gyr"],
        "rankable": serialized["rankable"],
        "risk_flags": serialized["risk_flags"],
        "missing_data": serialized["missing_data"],
    }


def export_ranked_csv(filepath: str, planets: list[dict]) -> None:
    """Export ranked planet rows to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for rank, planet in enumerate(planets, start=1):
            writer.writerow(csv_row(rank, planet))
    print(f"  Exported {filepath}")


def run_generate_data():
    """Main entry point for data generation."""
    print("=== Vigil Data Generation ===")

    planets_raw, source_desc = load_planets()
    print(f"  Loaded {len(planets_raw):,} planets from: {source_desc}")

    print("  Scoring planets...")
    scored = score_all(planets_raw)
    rankable = [p for p in scored if p.get("rankable") and p.get("composite_score") is not None]
    top_10_results = top_n(planets_raw, n=10)

    ensure_output_dirs()

    top_100_count = min(100, len(rankable))
    top_100 = [serialize_planet(p) for p in rankable[:top_100_count]]
    export_json("public/data/ranked_candidates.json", top_100)

    top_10_serialized = [serialize_planet(p) for p in top_10_results[:10]]
    export_json("public/data/top_10.json", top_10_serialized)

    now = datetime.now()
    site_meta = {
        "generated_at": now.isoformat(),
        "generated_date": now.strftime("%d %B %Y"),
        "source": source_desc,
        "total_planets_scanned": len(planets_raw),
        "rankable_candidates": len(rankable),
        "candidates_exported": len(top_100),
        "scoring_model_version": "Evidence-adjusted v2",
    }
    export_json("public/data/site_meta.json", site_meta)

    export_ranked_csv("data/ranked_candidates.csv", rankable)
    export_ranked_csv("public/data/ranked_candidates.csv", rankable)

    print("=== Data generation complete ===")
    print(f"  Total planets: {len(planets_raw):,}")
    print(f"  Rankable candidates: {len(rankable):,}")
    print(f"  Exported top {len(top_100)} JSON candidates")


if __name__ == "__main__":
    run_generate_data()
