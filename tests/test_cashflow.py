# tests/test_cashflows.py
from tco_core.cashflows import (
    annual_energy_cost_ice, annual_energy_cost_bev, annual_energy_cost_phev
)

def test_energy_cost_ice():
    # 15'000 km, 6.5 L/100, 2 CHF/L => 15000*0.065*2 = 1950
    v = annual_energy_cost_ice(15_000, 6.5, 2.0)
    assert abs(v - 1950.0) < 1e-9

def test_energy_cost_bev():
    # 15'000 km, 17 kWh/100, 0.23 CHF/kWh => 15000*0.17*0.23 = 586.5
    v = annual_energy_cost_bev(15_000, 17.0, 0.23)
    assert abs(v - 586.5) < 1e-9

def test_energy_cost_phev_mixture():
    # PHEV 60% elec : 0.6 * bev + 0.4 * ice
    ice = annual_energy_cost_ice(15_000 * 0.4, 6.5, 2.0)
    bev = annual_energy_cost_bev(15_000 * 0.6, 17.0, 0.23)
    mix = annual_energy_cost_phev(15_000, 6.5, 17.0, 0.6, 2.0, 0.23)
    assert abs(mix - (ice + bev)) < 1e-9
