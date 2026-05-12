"""
generate_data.py - Exports scored exoplanet data as machine-readable JSON.

Loads data/latest.csv (produced by scraper.py), scores all planets using
habitability.py, and exports:
- public/data/ranked_candidates.json (top 100+ scored planets)
- public/data/top_10.json (top 10 for quick access)
- public/data/site_meta.json (metadata: source, date, model version)

Falls back to sample data if latest.csv is not found.

Author: Rory
"""

import csv
import json
import os
from datetime import datetime
from habitability import score_all, top_n


SAMPLE_ROWS = [
    {"pl_name": "Kepler-442 b", "hostname": "Kepler-442", "sy_dist": "342", "pl_rade": "1.34", "pl_masse": "2.3", "pl_orbper": "112.3", "pl_orbsmax": "0.409", "pl_eqt": "233", "st_teff": "4402", "st_lum": "-0.22", "st_age": "5.2", "disc_year": "2015"},
    {"pl_name": "TOI-700 d", "hostname": "TOI-700", "sy_dist": "31.1", "pl_rade": "1.19", "pl_masse": "1.57", "pl_orbper": "37.4", "pl_orbsmax": "0.163", "pl_eqt": "269", "st_teff": "3480", "st_lum": "-1.51", "st_age": "8.0", "disc_year": "2020"},
    {"pl_name": "Proxima Cen b", "hostname": "Proxima Centauri", "sy_dist": "1.3", "pl_rade": "1.1", "pl_masse": "1.07", "pl_orbper": "11.2", "pl_orbsmax": "0.0485", "pl_eqt": "234", "st_teff": "3042", "st_lum": "-2.23", "st_age": "4.8", "disc_year": "2016"},
    {"pl_name": "TRAPPIST-1 e", "hostname": "TRAPPIST-1", "sy_dist": "12.1", "pl_rade": "0.92", "pl_masse": "0.69", "pl_orbper": "6.1", "pl_orbsmax": "0.0293", "pl_eqt": "251", "st_teff": "2566", "st_lum": "-3.25", "st_age": "7.6", "disc_year": "2017"},
    {"pl_name": "Kepler-62 f", "hostname": "Kepler-62", "sy_dist": "990", "pl_rade": "1.41", "pl_masse": "2.8", "pl_orbper": "267.3", "pl_orbsmax": "0.718", "pl_eqt": "208", "st_teff": "4925", "st_lum": "-0.59", "st_age": "7.0", "disc_year": "2013"},
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


def build_rank_explanation(planet: dict) -> str:
    """Build one concise explanation of why a candidate ranked where it did."""
    potential = planet.get("evidence_score")
    confidence = planet.get("data_confidence_score")
    ceiling = planet.get("habitability_ceiling")
    flags = planet.get("risk_flags", "").split(", ") if planet.get("risk_flags") and planet.get("risk_flags") != "none" else []
    missing = planet.get("missing_data", "").split(", ") if planet.get("missing_data") and planet.get("missing_data") != "none" else []

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


def serialize_planet(planet: dict) -> dict:
    """Convert planet dict to JSON-serializable format."""
    return {
        "pl_name": planet.get("pl_name", "Unknown"),
        "hostname": planet.get("hostname", "Unknown"),
        "sy_dist_pc": float(planet.get("sy_dist_pc")) if planet.get("sy_dist_pc") is not None else None,
        "disc_year": planet.get("disc_year", ""),
        "mass_me": float(planet.get("mass_me")) if planet.get("mass_me") is not None else None,
        "radius_re": float(planet.get("radius_re")) if planet.get("radius_re") is not None else None,
        "period_days": float(planet.get("period_days")) if planet.get("period_days") is not None else None,
        "sma_au": float(planet.get("sma_au")) if planet.get("sma_au") is not None else None,
        "eq_temp_k": float(planet.get("eq_temp_k")) if planet.get("eq_temp_k") is not None else None,
        "star_teff_k": float(planet.get("star_teff_k")) if planet.get("star_teff_k") is not None else None,
        "age_gyr": float(planet.get("age_gyr")) if planet.get("age_gyr") is not None else None,
        "score_magnetic_field": float(planet.get("score_magnetic_field")) if planet.get("score_magnetic_field") is not None else None,
        "score_habitable_zone": float(planet.get("score_habitable_zone")) if planet.get("score_habitable_zone") is not None else None,
        "score_rocky_likelihood": float(planet.get("score_rocky_likelihood")) if planet.get("score_rocky_likelihood") is not None else None,
        "score_stellar_stability": float(planet.get("score_stellar_stability")) if planet.get("score_stellar_stability") is not None else None,
        "score_system_age": float(planet.get("score_system_age")) if planet.get("score_system_age") is not None else None,
        "score_atmosphere_hold": float(planet.get("score_atmosphere_hold")) if planet.get("score_atmosphere_hold") is not None else None,
        "score_thermal_plausibility": float(planet.get("score_thermal_plausibility")) if planet.get("score_thermal_plausibility") is not None else None,
        "evidence_score": float(planet.get("evidence_score")) if planet.get("evidence_score") is not None else None,
        "data_confidence_score": float(planet.get("data_confidence_score")) if planet.get("data_confidence_score") is not None else None,
        "habitability_ceiling": float(planet.get("habitability_ceiling")) if planet.get("habitability_ceiling") is not None else None,
        "composite_score": float(planet.get("composite_score")) if planet.get("composite_score") is not None else None,
        "rankable": planet.get("rankable", False),
        "risk_flags": planet.get("risk_flags", "none"),
        "missing_data": planet.get("missing_data", "none"),
        "rank_explanation": build_rank_explanation(planet),
    }


def ensure_output_dir():
    """Create public/data directory if it does not exist."""
    os.makedirs("public/data", exist_ok=True)


def export_json(filepath: str, data: dict | list) -> None:
    """Export data as JSON with nice formatting."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  Exported {filepath}")


def run_generate_data():
    """Main entry point for data generation."""
    print("=== Vigil Data Generation ===")

    # Load planets
    planets_raw, source_desc = load_planets()
    print(f"  Loaded {len(planets_raw):,} planets from: {source_desc}")

    # Score all
    print("  Scoring planets...")
    scored = score_all(planets_raw)

    # Filter and prepare
    rankable = [p for p in scored if p.get("rankable") and p.get("composite_score") is not None]
    top_10_results = top_n(planets_raw, n=10)

    # Prepare output directories
    ensure_output_dir()

    # Export top 100 (or all rankable if fewer)
    top_100_count = min(100, len(rankable))
    top_100 = [serialize_planet(p) for p in rankable[:top_100_count]]
    export_json("public/data/ranked_candidates.json", top_100)

    # Export top 10
    top_10_serialized = [serialize_planet(p) for p in top_10_results[:10]]
    export_json("public/data/top_10.json", top_10_serialized)

    # Export site metadata
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

    print("=== Data generation complete ===")
    print(f"  Total planets: {len(planets_raw):,}")
    print(f"  Rankable candidates: {len(rankable):,}")
    print(f"  Exported top {len(top_100)}")


if __name__ == "__main__":
    run_generate_data()
