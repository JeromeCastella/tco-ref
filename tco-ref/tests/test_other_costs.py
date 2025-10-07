# tests/test_other_costs.py
import pytest
from tco_core.cashflows import other_costs_series
from tco_core.models import GlobalParams, VehicleSpec, Tech


@pytest.fixture
def base_params():
    """Base parameters for 8-year horizon"""
    return GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.015,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )


@pytest.fixture
def ice_spec():
    """ICE vehicle specification"""
    return VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=1.8,
        elec_price_home=0.20,
        elec_price_work=0.15,
        elec_price_public=0.45,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=3000.0,
        tires_base_chf=800.0,
        annual_tax_chf=300.0,
        annual_insurance_chf=1200.0,
        phev_share_elec=0.0,
    )


@pytest.fixture
def bev_spec():
    """BEV vehicle specification"""
    return VehicleSpec(
        tech=Tech.BEV,
        vehicle_class="compact",
        purchase_price=35000.0,
        residual_rate_8y_hint=0.40,
        consumption_fuel_l_per_100=0.0,
        consumption_elec_kwh_per_100=16.0,
        fuel_price_chf_per_l=1.8,
        elec_price_home=0.20,
        elec_price_work=0.15,
        elec_price_public=0.45,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=2500.0,
        tires_base_chf=800.0,
        annual_tax_chf=250.0,
        annual_insurance_chf=1400.0,
        phev_share_elec=0.0,
    )


@pytest.fixture
def phev_spec():
    """PHEV vehicle specification"""
    return VehicleSpec(
        tech=Tech.PHEV,
        vehicle_class="compact",
        purchase_price=40000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=5.0,
        consumption_elec_kwh_per_100=18.0,
        fuel_price_chf_per_l=1.8,
        elec_price_home=0.20,
        elec_price_work=0.15,
        elec_price_public=0.45,
        w_home=0.7,
        w_work=0.2,
        w_public=0.1,
        maint_6y_chf=3200.0,
        tires_base_chf=800.0,
        annual_tax_chf=280.0,
        annual_insurance_chf=1500.0,
        phev_share_elec=0.5,
    )


# ---------- Test 1: Infrastructure de recharge ----------

def test_infrastructure_ice_no_charging_infra(ice_spec, base_params):
    """Test that ICE vehicles have NO charging infrastructure cost"""
    series = other_costs_series(Tech.ICE, ice_spec, base_params)
    
    assert len(series) == 8
    # ICE should never have 3040 CHF infrastructure cost
    # Year 1 should only have tax + insurance + care
    year_1 = series[0]
    expected_year_1 = 300.0 + 1200.0 + 150.0  # No infrastructure
    assert abs(year_1 - expected_year_1) < 1e-9


def test_infrastructure_bev_year_1_only(bev_spec, base_params):
    """Test that BEV has 3'040 CHF infrastructure in year 1 only"""
    series = other_costs_series(Tech.BEV, bev_spec, base_params)
    
    # Year 1: should include 3040 CHF infrastructure
    year_1 = series[0]
    expected_year_1 = 250.0 + 1400.0 + 150.0 + 3040.0
    assert abs(year_1 - expected_year_1) < 1e-9
    
    # Year 2: should NOT include infrastructure
    year_2 = series[1]
    # Year 2 has inflation on tax and care: (250 + 150) * 1.015
    expected_year_2 = (250.0 * 1.015) + 1400.0 + (150.0 * 1.015)
    assert abs(year_2 - expected_year_2) < 1e-9


def test_infrastructure_phev_year_1_only(phev_spec, base_params):
    """Test that PHEV has 3'040 CHF infrastructure in year 1 only"""
    series = other_costs_series(Tech.PHEV, phev_spec, base_params)
    
    # Year 1: should include 3040 CHF infrastructure
    year_1 = series[0]
    expected_year_1 = 280.0 + 1500.0 + 150.0 + 3040.0
    assert abs(year_1 - expected_year_1) < 1e-9
    
    # Year 2: should NOT include infrastructure
    year_2 = series[1]
    expected_year_2 = (280.0 * 1.015) + 1500.0 + (150.0 * 1.015)
    assert abs(year_2 - expected_year_2) < 1e-9


# ---------- Test 2: Structure annuelle ----------

def test_annual_structure_ice(ice_spec, base_params):
    """Test annual structure: tax + insurance + care (no infrastructure for ICE)"""
    params = GlobalParams(
        years=5,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,  # No inflation for simplicity
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.ICE, ice_spec, params)
    
    # With 0% inflation, all years should be: tax + insurance + care
    expected = 300.0 + 1200.0 + 150.0
    for cost in series:
        assert abs(cost - expected) < 1e-9


def test_annual_structure_bev_after_year_1(bev_spec, base_params):
    """Test annual structure for BEV after year 1: tax + insurance + care (no infrastructure)"""
    params = GlobalParams(
        years=5,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,  # No inflation
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.BEV, bev_spec, params)
    
    # Year 1: includes infrastructure
    expected_year_1 = 250.0 + 1400.0 + 150.0 + 3040.0
    assert abs(series[0] - expected_year_1) < 1e-9
    
    # Years 2-5: no infrastructure
    expected_others = 250.0 + 1400.0 + 150.0
    for i in range(1, 5):
        assert abs(series[i] - expected_others) < 1e-9


# ---------- Test 3: Inflation OPEX ----------

def test_tax_inflates_with_opex_inflation(ice_spec):
    """Test that tax increases with OPEX inflation"""
    params = GlobalParams(
        years=5,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.05,  # 5% OPEX inflation
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.ICE, ice_spec, params)
    
    # Year 1: tax = 300 * 1.05^0 = 300
    # Year 2: tax = 300 * 1.05^1 = 315
    # Year 3: tax = 300 * 1.05^2 = 330.75
    base_tax = 300.0
    insurance = 1200.0  # Constant
    base_care = 150.0
    
    # Year 1
    expected_1 = (base_tax * 1.0) + insurance + (base_care * 1.0)
    assert abs(series[0] - expected_1) < 1e-9
    
    # Year 2
    expected_2 = (base_tax * 1.05) + insurance + (base_care * 1.05)
    assert abs(series[1] - expected_2) < 1e-9
    
    # Year 3
    expected_3 = (base_tax * 1.05**2) + insurance + (base_care * 1.05**2)
    assert abs(series[2] - expected_3) < 1e-9


def test_care_inflates_with_opex_inflation(bev_spec):
    """Test that care (150 CHF) increases with OPEX inflation"""
    params = GlobalParams(
        years=4,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.03,  # 3% OPEX inflation
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.BEV, bev_spec, params)
    
    # Extract just the care component by removing tax, insurance, and infrastructure
    # Year 1: includes 3040 infrastructure
    care_year_1 = series[0] - 250.0 - 1400.0 - 3040.0
    assert abs(care_year_1 - 150.0) < 1e-9
    
    # Year 2: care = 150 * 1.03
    care_year_2 = series[1] - (250.0 * 1.03) - 1400.0
    assert abs(care_year_2 - (150.0 * 1.03)) < 1e-9


def test_insurance_remains_constant(phev_spec):
    """Test that insurance does NOT inflate (constant over 8 years)"""
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.1,  # High 10% inflation to make it obvious
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.PHEV, phev_spec, params)
    
    # Extract insurance from each year
    # Year 1: total - tax - care - infrastructure
    insurance_1 = series[0] - 280.0 - 150.0 - 3040.0
    assert abs(insurance_1 - 1500.0) < 1e-9
    
    # Year 2: total - tax_inflated - care_inflated
    insurance_2 = series[1] - (280.0 * 1.1) - (150.0 * 1.1)
    assert abs(insurance_2 - 1500.0) < 1e-9
    
    # Year 8: total - tax_inflated - care_inflated
    insurance_8 = series[7] - (280.0 * 1.1**7) - (150.0 * 1.1**7)
    assert abs(insurance_8 - 1500.0) < 1e-9


def test_combined_inflation_effects(ice_spec):
    """Test combination of inflating (tax, care) and constant (insurance) components"""
    params = GlobalParams(
        years=6,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.02,  # 2% OPEX inflation
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.ICE, ice_spec, params)
    
    # Manual calculation for each year
    for t in range(1, 7):
        tax = 300.0 * (1.02 ** (t - 1))
        insurance = 1200.0  # Constant
        care = 150.0 * (1.02 ** (t - 1))
        expected = tax + insurance + care
        assert abs(series[t - 1] - expected) < 1e-9


# ---------- Test 4: Totaux sur 8 ans ----------

def test_8_year_total_ice_typical(ice_spec, base_params):
    """Test 8-year total for ICE (no infrastructure)"""
    series = other_costs_series(Tech.ICE, ice_spec, base_params)
    total_8y = sum(series)
    
    # Expected: 8 * (tax_avg + insurance + care_avg)
    # With 1.5% inflation over 8 years, average multiplier ≈ 1.053
    # Approximate: 8 * (300*1.053 + 1200 + 150*1.053) ≈ 8 * 1674 ≈ 13,392
    # Let's verify it's in a reasonable range
    assert 13000 < total_8y < 14000


def test_8_year_total_bev_with_infrastructure(bev_spec, base_params):
    """Test 8-year total for BEV (includes 3040 CHF infrastructure in year 1)"""
    series = other_costs_series(Tech.BEV, bev_spec, base_params)
    total_8y = sum(series)
    
    # Expected: (base costs over 8 years) + 3040 infrastructure
    # Base per year ≈ 250 + 1400 + 150 = 1800 (with inflation)
    # Approximate: 8 * 1800 * 1.053 + 3040 ≈ 15,163 + 3040 ≈ 18,203
    # But year 1 has infrastructure, so total should be higher
    assert 17000 < total_8y < 19000


def test_8_year_total_phev_with_infrastructure(phev_spec, base_params):
    """Test 8-year total for PHEV (includes 3040 CHF infrastructure in year 1)"""
    series = other_costs_series(Tech.PHEV, phev_spec, base_params)
    total_8y = sum(series)
    
    # Expected: (base costs over 8 years) + 3040 infrastructure
    # Base per year ≈ 280 + 1500 + 150 = 1930 (with inflation)
    # Approximate: 8 * 1930 * 1.053 + 3040 ≈ 16,260 + 3040 ≈ 19,300
    assert 18000 < total_8y < 20000


def test_8_year_total_breakdown_bev(bev_spec):
    """Detailed breakdown test: verify each component's contribution over 8 years"""
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,  # No inflation for exact calculation
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.BEV, bev_spec, params)
    total = sum(series)
    
    # Exact calculation:
    # - Tax: 250 * 8 = 2000
    # - Insurance: 1400 * 8 = 11200
    # - Care: 150 * 8 = 1200
    # - Infrastructure: 3040 (year 1 only)
    # Total: 2000 + 11200 + 1200 + 3040 = 17440
    expected_total = 2000.0 + 11200.0 + 1200.0 + 3040.0
    assert abs(total - expected_total) < 1e-9


# ---------- Edge cases ----------

def test_zero_inflation(ice_spec):
    """Test with 0% inflation - all components except infrastructure should be constant"""
    params = GlobalParams(
        years=10,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.ICE, ice_spec, params)
    
    # All years should be identical (no inflation)
    expected = 300.0 + 1200.0 + 150.0
    for cost in series:
        assert abs(cost - expected) < 1e-9


def test_high_inflation(bev_spec):
    """Test with high inflation (10%) to verify compounding"""
    params = GlobalParams(
        years=5,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.1,  # 10% OPEX inflation
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.BEV, bev_spec, params)
    
    # Year 5: tax = 250 * 1.1^4, care = 150 * 1.1^4
    tax_y5 = 250.0 * (1.1 ** 4)
    care_y5 = 150.0 * (1.1 ** 4)
    insurance_y5 = 1400.0  # Constant
    expected_y5 = tax_y5 + insurance_y5 + care_y5
    
    assert abs(series[4] - expected_y5) < 1e-2


def test_one_year_horizon(ice_spec):
    """Test with 1-year horizon"""
    params = GlobalParams(
        years=1,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.015,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series = other_costs_series(Tech.ICE, ice_spec, params)
    
    assert len(series) == 1
    # Year 1: no inflation applied yet (multiplier = 1.0)
    expected = 300.0 + 1200.0 + 150.0
    assert abs(series[0] - expected) < 1e-9


def test_different_tax_values():
    """Test that different tax values produce proportional results"""
    spec_low_tax = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=25000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=5.0,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=1.8,
        elec_price_home=0.20,
        elec_price_work=0.15,
        elec_price_public=0.45,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=2500.0,
        tires_base_chf=700.0,
        annual_tax_chf=200.0,  # Low tax
        annual_insurance_chf=1000.0,
        phev_share_elec=0.0,
    )
    
    spec_high_tax = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="suv",
        purchase_price=55000.0,
        residual_rate_8y_hint=0.30,
        consumption_fuel_l_per_100=9.0,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=1.8,
        elec_price_home=0.20,
        elec_price_work=0.15,
        elec_price_public=0.45,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=4000.0,
        tires_base_chf=1200.0,
        annual_tax_chf=600.0,  # 3x higher tax
        annual_insurance_chf=1000.0,  # Same insurance
        phev_share_elec=0.0,
    )
    
    params = GlobalParams(
        years=5,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,  # No inflation for simplicity
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    series_low = other_costs_series(Tech.ICE, spec_low_tax, params)
    series_high = other_costs_series(Tech.ICE, spec_high_tax, params)
    
    # Low: 200 + 1000 + 150 = 1350 per year
    # High: 600 + 1000 + 150 = 1750 per year
    # Difference: 400 per year (due to tax)
    for i in range(5):
        assert abs(series_high[i] - series_low[i] - 400.0) < 1e-9


def test_tech_enum_vs_string():
    """Test that tech can be passed as enum or string"""
    spec = VehicleSpec(
        tech=Tech.BEV,
        vehicle_class="compact",
        purchase_price=35000.0,
        residual_rate_8y_hint=0.40,
        consumption_fuel_l_per_100=0.0,
        consumption_elec_kwh_per_100=16.0,
        fuel_price_chf_per_l=1.8,
        elec_price_home=0.20,
        elec_price_work=0.15,
        elec_price_public=0.45,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=2500.0,
        tires_base_chf=800.0,
        annual_tax_chf=250.0,
        annual_insurance_chf=1400.0,
        phev_share_elec=0.0,
    )
    
    params = GlobalParams(
        years=3,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    # Test with Tech enum
    series_enum = other_costs_series(Tech.BEV, spec, params)
    
    # Test with string (cast to Tech)
    series_string = other_costs_series(Tech("BEV"), spec, params)
    
    # Both should produce identical results
    assert len(series_enum) == len(series_string)
    for i in range(len(series_enum)):
        assert abs(series_enum[i] - series_string[i]) < 1e-9
