# tests/test_cashflows.py
from tco_core.cashflows import (
    annual_energy_cost_ice, annual_energy_cost_bev, annual_energy_cost_phev,
    build_energy_price_series
)
from tco_core.models import Tech, GlobalParams, VehicleSpec
from tco_core.energy import weighted_electricity_price

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


# ========== COMPREHENSIVE PHEV TESTS ==========

def test_phev_0_percent_electric():
    """PHEV with 0% electric share should equal pure ICE cost"""
    km = 15_000
    l_per_100 = 6.5
    kwh_per_100 = 17.0
    fuel_price = 2.0
    elec_price = 0.23
    
    ice_cost = annual_energy_cost_ice(km, l_per_100, fuel_price)
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, 0.0, fuel_price, elec_price)
    
    assert abs(phev_cost - ice_cost) < 1e-9, "PHEV with 0% elec should equal ICE cost"


def test_phev_100_percent_electric():
    """PHEV with 100% electric share should equal pure BEV cost"""
    km = 15_000
    l_per_100 = 6.5
    kwh_per_100 = 17.0
    fuel_price = 2.0
    elec_price = 0.23
    
    bev_cost = annual_energy_cost_bev(km, kwh_per_100, elec_price)
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, 1.0, fuel_price, elec_price)
    
    assert abs(phev_cost - bev_cost) < 1e-9, "PHEV with 100% elec should equal BEV cost"


def test_phev_25_percent_electric():
    """PHEV with 25% electric share"""
    km = 15_000
    l_per_100 = 6.5
    kwh_per_100 = 17.0
    fuel_price = 2.0
    elec_price = 0.23
    share_elec = 0.25
    
    expected_elec = annual_energy_cost_bev(km * share_elec, kwh_per_100, elec_price)
    expected_ice = annual_energy_cost_ice(km * (1 - share_elec), l_per_100, fuel_price)
    expected_total = expected_elec + expected_ice
    
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, elec_price)
    
    assert abs(phev_cost - expected_total) < 1e-9


def test_phev_50_percent_electric():
    """PHEV with 50% electric share (typical PHEV usage)"""
    km = 15_000
    l_per_100 = 6.5
    kwh_per_100 = 17.0
    fuel_price = 2.0
    elec_price = 0.23
    share_elec = 0.5
    
    expected_elec = annual_energy_cost_bev(km * share_elec, kwh_per_100, elec_price)
    expected_ice = annual_energy_cost_ice(km * (1 - share_elec), l_per_100, fuel_price)
    expected_total = expected_elec + expected_ice
    
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, elec_price)
    
    assert abs(phev_cost - expected_total) < 1e-9


def test_phev_75_percent_electric():
    """PHEV with 75% electric share (high electric usage)"""
    km = 15_000
    l_per_100 = 6.5
    kwh_per_100 = 17.0
    fuel_price = 2.0
    elec_price = 0.23
    share_elec = 0.75
    
    expected_elec = annual_energy_cost_bev(km * share_elec, kwh_per_100, elec_price)
    expected_ice = annual_energy_cost_ice(km * (1 - share_elec), l_per_100, fuel_price)
    expected_total = expected_elec + expected_ice
    
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, elec_price)
    
    assert abs(phev_cost - expected_total) < 1e-9


def test_phev_with_100_percent_home_charging():
    """PHEV with 100% home charging at 0.20 CHF/kWh"""
    km = 15_000
    share_elec = 0.5
    kwh_per_100 = 17.0
    l_per_100 = 6.5
    fuel_price = 2.0
    
    # 100% home charging
    elec_price_home = 0.20
    weighted_price = elec_price_home  # 100% home
    
    expected_elec = (kwh_per_100 / 100.0) * (km * share_elec) * weighted_price
    expected_ice = (l_per_100 / 100.0) * (km * (1 - share_elec)) * fuel_price
    expected_total = expected_elec + expected_ice
    
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, weighted_price)
    
    assert abs(phev_cost - expected_total) < 1e-9


def test_phev_with_100_percent_public_charging():
    """PHEV with 100% public charging at 0.50 CHF/kWh (expensive)"""
    km = 15_000
    share_elec = 0.5
    kwh_per_100 = 17.0
    l_per_100 = 6.5
    fuel_price = 2.0
    
    # 100% public charging (expensive)
    elec_price_public = 0.50
    weighted_price = elec_price_public  # 100% public
    
    expected_elec = (kwh_per_100 / 100.0) * (km * share_elec) * weighted_price
    expected_ice = (l_per_100 / 100.0) * (km * (1 - share_elec)) * fuel_price
    expected_total = expected_elec + expected_ice
    
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, weighted_price)
    
    assert abs(phev_cost - expected_total) < 1e-9


def test_phev_with_mixed_charging_profile():
    """PHEV with mixed charging: 50% home @ 0.20, 50% public @ 0.50 → 0.35 weighted"""
    km = 15_000
    share_elec = 0.5
    kwh_per_100 = 17.0
    l_per_100 = 6.5
    fuel_price = 2.0
    
    # Mixed charging profile
    elec_home = 0.20
    elec_public = 0.50
    w_home = 0.5
    w_public = 0.5
    weighted_price = (w_home * elec_home) + (w_public * elec_public)  # = 0.35
    
    assert abs(weighted_price - 0.35) < 1e-9, "Weighted price should be 0.35"
    
    expected_elec = (kwh_per_100 / 100.0) * (km * share_elec) * weighted_price
    expected_ice = (l_per_100 / 100.0) * (km * (1 - share_elec)) * fuel_price
    expected_total = expected_elec + expected_ice
    
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, weighted_price)
    
    assert abs(phev_cost - expected_total) < 1e-9


def test_phev_weighted_price_impact():
    """Test that PHEV electric cost varies with weighted electricity price"""
    km = 15_000
    share_elec = 0.5
    kwh_per_100 = 17.0
    l_per_100 = 6.5
    fuel_price = 2.0
    
    # Cheap home charging
    phev_cost_cheap = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, 0.20)
    
    # Expensive public charging
    phev_cost_expensive = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, 0.50)
    
    # The expensive charging should cost more
    assert phev_cost_expensive > phev_cost_cheap, "Public charging should cost more than home"
    
    # Calculate expected difference (only affects electric portion)
    price_diff = 0.50 - 0.20  # 0.30 CHF/kWh difference
    km_elec = km * share_elec
    expected_diff = (kwh_per_100 / 100.0) * km_elec * price_diff
    actual_diff = phev_cost_expensive - phev_cost_cheap
    
    assert abs(actual_diff - expected_diff) < 1e-9


def test_phev_thermal_portion_independent_of_elec_price():
    """Test that PHEV thermal portion cost is independent of electricity price"""
    km = 15_000
    share_elec = 0.5
    kwh_per_100 = 17.0
    l_per_100 = 6.5
    fuel_price = 2.0
    
    # Test with different electricity prices
    phev_cost_1 = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, 0.20)
    phev_cost_2 = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, 0.50)
    
    # The difference should only be in the electric portion
    expected_thermal = (l_per_100 / 100.0) * (km * (1 - share_elec)) * fuel_price
    
    elec_cost_1 = (kwh_per_100 / 100.0) * (km * share_elec) * 0.20
    elec_cost_2 = (kwh_per_100 / 100.0) * (km * share_elec) * 0.50
    
    assert abs((phev_cost_1 - elec_cost_1) - expected_thermal) < 1e-9
    assert abs((phev_cost_2 - elec_cost_2) - expected_thermal) < 1e-9


def test_build_energy_price_series_with_phev():
    """Test that build_energy_price_series correctly calculates weighted electricity price"""
    spec = VehicleSpec(
        tech=Tech.PHEV,
        vehicle_class="midsize",
        purchase_price=45000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=17.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.20,
        elec_price_work=0.20,
        elec_price_public=0.50,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=3000.0,
        tires_base_chf=800.0,
        phev_share_elec=0.5,
    )
    
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,  # No inflation for easier testing
        opex_inflation=0.0,
    )
    
    fuel_series, elec_series = build_energy_price_series(spec, params, 8)
    
    # Calculate expected weighted price
    expected_weighted = weighted_electricity_price(
        0.20, 0.20, 0.50,  # prices
        0.9, 0.0, 0.1      # weights
    )
    # 0.9 * 0.20 + 0.0 * 0.20 + 0.1 * 0.50 = 0.18 + 0 + 0.05 = 0.23
    assert abs(expected_weighted - 0.23) < 1e-9
    
    # Check that all years have the same price (no inflation)
    assert len(elec_series) == 8
    for price in elec_series:
        assert abs(price - expected_weighted) < 1e-9
    
    # Check fuel series
    assert len(fuel_series) == 8
    for price in fuel_series:
        assert abs(price - 2.0) < 1e-9


def test_phev_complex_charging_profile():
    """Test PHEV with realistic complex charging profile: 70% home, 20% work, 10% public"""
    km = 15_000
    share_elec = 0.6
    kwh_per_100 = 17.0
    l_per_100 = 6.5
    fuel_price = 2.0
    
    # Complex charging profile
    elec_home = 0.20
    elec_work = 0.20
    elec_public = 0.50
    w_home = 0.7
    w_work = 0.2
    w_public = 0.1
    
    weighted_price = weighted_electricity_price(
        elec_home, elec_work, elec_public,
        w_home, w_work, w_public
    )
    # 0.7 * 0.20 + 0.2 * 0.20 + 0.1 * 0.50 = 0.14 + 0.04 + 0.05 = 0.23
    assert abs(weighted_price - 0.23) < 1e-9
    
    expected_elec = (kwh_per_100 / 100.0) * (km * share_elec) * weighted_price
    expected_ice = (l_per_100 / 100.0) * (km * (1 - share_elec)) * fuel_price
    expected_total = expected_elec + expected_ice
    
    phev_cost = annual_energy_cost_phev(km, l_per_100, kwh_per_100, share_elec, fuel_price, weighted_price)
    
    assert abs(phev_cost - expected_total) < 1e-9
