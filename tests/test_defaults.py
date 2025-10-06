import math

import pytest

from tco_core.defaults import get_defaults, load_defaults_by_class, residual_rate_from_defaults
from tco_core.models import Tech


@pytest.fixture(scope="module")
def defaults():
    return load_defaults_by_class()


def test_load_defaults_structure(defaults):
    classes = {"mini", "compact", "midsize", "suv"}
    assert classes.issubset(defaults.keys())

    for vehicle_class in classes:
        tech_defaults = defaults[vehicle_class]
        for tech in ["ICE", "BEV", "PHEV"]:
            assert tech in tech_defaults
            values = tech_defaults[tech]
            assert "purchase_price" in values
            assert "residual_rate_8y_hint" in values or "residual_rate_8y" in values
            assert "maint_6y_chf" in values
            assert "tires_base_chf" in values
            if tech != "BEV":
                assert "consumption_fuel_l_per_100" in values
            if tech != "ICE":
                assert "consumption_elec_kwh_per_100" in values


def test_get_defaults_by_class_and_tech(defaults):
    midsize_bev = get_defaults(Tech.BEV, "midsize", defaults)
    assert midsize_bev == defaults["midsize"]["BEV"]

    suv_phev = get_defaults("phev", "SUV", defaults)
    assert math.isclose(suv_phev["consumption_elec_kwh_per_100"], 19.0)
    assert math.isclose(suv_phev["purchase_price"], 65_000)


def test_make_spec_uses_defaults():
    from app.app import make_spec  # import inside test to avoid heavy streamlit setup at module import time

    midsize_defaults = load_defaults_by_class()["midsize"]["PHEV"]
    spec = make_spec(Tech.PHEV, "midsize")
    assert spec.vehicle_class == "midsize"
    assert math.isclose(spec.purchase_price, midsize_defaults["purchase_price"])
    assert math.isclose(spec.maint_6y_chf, midsize_defaults["maint_6y_chf"])
    assert math.isclose(spec.tires_base_chf, midsize_defaults["tires_base_chf"])
    assert math.isclose(spec.consumption_fuel_l_per_100, midsize_defaults["consumption_fuel_l_per_100"])
    assert math.isclose(spec.consumption_elec_kwh_per_100, midsize_defaults["consumption_elec_kwh_per_100"])
    assert math.isclose(spec.residual_rate_8y, residual_rate_from_defaults(midsize_defaults))
