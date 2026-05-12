from habitability import habitability_ceiling, score_planet


def make_planet(**overrides):
    row = {
        "pl_name": "Test Planet",
        "hostname": "Test Star",
        "sy_dist": "10",
        "pl_rade": "1.0",
        "pl_masse": "1.0",
        "pl_orbper": "365.25",
        "pl_orbsmax": "1.0",
        "pl_eqt": "255",
        "st_teff": "5778",
        "st_lum": "0",
        "st_age": "4.5",
        "disc_year": "2026",
    }
    row.update(overrides)
    return row


def test_ultra_short_period_planets_are_capped():
    result = score_planet(make_planet(pl_orbper="0.8", pl_orbsmax="0.01", pl_eqt="1200"))

    assert result["habitability_ceiling"] <= 1.5
    assert "ultra-short orbit" in result["risk_flags"]


def test_gas_giant_size_planets_are_capped():
    ceiling, flags = habitability_ceiling(
        radius_re=12.0,
        period_days=365.25,
        sma_au=1.0,
        eq_temp_k=255.0,
        star_teff_k=5778.0,
    )

    assert ceiling <= 2.0
    assert "gas-giant-size radius" in flags


def test_missing_data_reduces_confidence():
    complete = score_planet(make_planet())
    incomplete = score_planet(
        make_planet(
            pl_masse="",
            pl_rade="",
            pl_orbsmax="",
            pl_eqt="",
            st_age="",
            sy_dist="",
        )
    )

    assert incomplete["data_confidence_score"] < complete["data_confidence_score"]
    assert "mass missing" in incomplete["risk_flags"]
    assert "radius missing" in incomplete["risk_flags"]


def test_temperate_earth_like_candidate_beats_hot_close_in_world():
    temperate = score_planet(make_planet())
    hot_close_in = score_planet(
        make_planet(
            pl_name="Hot Test World",
            pl_orbper="0.9",
            pl_orbsmax="0.015",
            pl_eqt="1400",
        )
    )

    assert temperate["composite_score"] > hot_close_in["composite_score"]
    assert hot_close_in["habitability_ceiling"] <= 1.5
