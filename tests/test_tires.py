import pytest
from tco_core.tires import tires_series, TIRE_REPLACEMENT_INTERVAL_KM
from tco_core.models import GlobalParams, VehicleSpec, Tech


@pytest.fixture
def base_params():
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
def base_spec():
    return VehicleSpec(
        tech=Tech.BEV,
        vehicle_class="compact",
        purchase_price=35000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=0.0,
        consumption_elec_kwh_per_100=16.0,
        fuel_price_chf_per_l=1.8,
        elec_price_home=0.20,
        elec_price_work=0.15,
        elec_price_public=0.45,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=3000.0,
        tires_base_chf=800.0,
        phev_share_elec=0.5,
    )


def test_discrete_replacement_single(base_spec, base_params):
    """Test single replacement scenario: 10k km/year × 3 years = 30k km → 0 replacements (under 40k)"""
    params = GlobalParams(
        years=3,
        km_per_year=10000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.015,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    assert len(result) == 3
    assert sum(result) == 0.0


def test_discrete_replacement_one_replacement(base_spec, base_params):
    """Test 1 replacement: 15k km/year × 3 years = 45k km → 1 replacement at 40k (year 3)"""
    params = GlobalParams(
        years=3,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    assert len(result) == 3
    assert result[0] == 0.0
    assert result[1] == 0.0
    base_cost = 800.0 * 2.0
    assert abs(result[2] - base_cost) < 0.01


def test_discrete_replacement_multiple(base_spec, base_params):
    """Test 3 replacements: 15k km/year × 8 years = 120k km → 3 replacements"""
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    assert len(result) == 8
    base_cost = 800.0 * 2.0
    
    # Year 3: 40k km reached (40k / 15k = 2.67 → ceil = 3)
    assert abs(result[2] - base_cost) < 0.01
    
    # Year 6: 80k km reached (80k / 15k = 5.33 → ceil = 6)
    assert abs(result[5] - base_cost) < 0.01
    
    # Year 8: 120k km reached (120k / 15k = 8.0)
    assert abs(result[7] - base_cost) < 0.01
    
    # Other years should be 0
    assert result[0] == 0.0
    assert result[1] == 0.0
    assert result[3] == 0.0
    assert result[4] == 0.0
    assert result[6] == 0.0


def test_different_km_per_year_10k(base_spec):
    """Test with 10k km/year × 8 years = 80k km → 2 replacements"""
    params = GlobalParams(
        years=8,
        km_per_year=10000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    base_cost = 800.0 * 2.0
    
    # 40k at year 4, 80k at year 8
    assert abs(result[3] - base_cost) < 0.01
    assert abs(result[7] - base_cost) < 0.01
    
    # Count non-zero entries
    non_zero = [x for x in result if x > 0]
    assert len(non_zero) == 2


def test_different_km_per_year_20k(base_spec):
    """Test with 20k km/year × 8 years = 160k km → 4 replacements"""
    params = GlobalParams(
        years=8,
        km_per_year=20000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # Count non-zero entries (should be 4 replacements)
    non_zero = [x for x in result if x > 0]
    assert len(non_zero) == 4


def test_different_km_per_year_30k(base_spec):
    """Test with 30k km/year × 8 years = 240k km → 6 replacements"""
    params = GlobalParams(
        years=8,
        km_per_year=30000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # Count non-zero entries (should be 6 replacements)
    non_zero = [x for x in result if x > 0]
    assert len(non_zero) == 6


def test_different_horizon_3_years(base_spec):
    """Test with 3-year horizon"""
    params = GlobalParams(
        years=3,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    assert len(result) == 3


def test_different_horizon_15_years(base_spec):
    """Test with 15-year horizon: 15k km/year × 15 years = 225k km → 5 replacements"""
    params = GlobalParams(
        years=15,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    assert len(result) == 15
    # Count non-zero entries (5 replacements: 40k, 80k, 120k, 160k, 200k)
    # 225k / 40k = 5.625 → ceil(5.625) = 6, but only 5 full replacements within 225k
    non_zero = [x for x in result if x > 0]
    assert len(non_zero) == 5


def test_include_tires_x2_true(base_spec):
    """Test with include_tires_x2=True (multiplier = 2)"""
    params = GlobalParams(
        years=3,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # One replacement at year 3, cost should be 800 * 2
    expected_cost = 800.0 * 2.0
    assert abs(result[2] - expected_cost) < 0.01


def test_include_tires_x2_false(base_spec):
    """Test with include_tires_x2=False (multiplier = 1)"""
    params = GlobalParams(
        years=3,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=False,
    )
    
    result = tires_series(base_spec, params)
    
    # One replacement at year 3, cost should be 800 * 1
    expected_cost = 800.0 * 1.0
    assert abs(result[2] - expected_cost) < 0.01


def test_opex_inflation_application(base_spec):
    """Test OPEX inflation is applied correctly for replacement years"""
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.10,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    base_cost = 800.0 * 2.0
    
    # Year 3 (index 2): inflation factor = (1.10)^(3-1) = 1.21
    expected_year_3 = base_cost * (1.10 ** 2)
    assert abs(result[2] - expected_year_3) < 0.01
    
    # Year 6 (index 5): inflation factor = (1.10)^(6-1) = 1.61051
    expected_year_6 = base_cost * (1.10 ** 5)
    assert abs(result[5] - expected_year_6) < 0.01
    
    # Year 8 (index 7): inflation factor = (1.10)^(8-1) = 1.9487171
    expected_year_8 = base_cost * (1.10 ** 7)
    assert abs(result[7] - expected_year_8) < 0.01


def test_edge_case_very_low_km(base_spec):
    """Test edge case: very low km (5k km/year × 8 years = 40k km → 1 replacement)"""
    params = GlobalParams(
        years=8,
        km_per_year=5000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # Only 1 replacement at exactly 40k km (year 8)
    non_zero = [x for x in result if x > 0]
    assert len(non_zero) == 1
    assert result[7] > 0


def test_edge_case_very_high_km(base_spec):
    """Test edge case: very high km (50k km/year × 8 years = 400k km → 10 replacements)"""
    params = GlobalParams(
        years=8,
        km_per_year=50000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # 400k / 40k = 10 replacements
    non_zero = [x for x in result if x > 0]
    assert len(non_zero) == 8
    
    # Total cost should be 10 × base_cost (spread across 8 years)
    base_cost = 800.0 * 2.0
    assert abs(sum(result) - (10 * base_cost)) < 0.01


def test_zero_costs_in_non_replacement_years(base_spec):
    """Test that costs are exactly 0 in years without replacement"""
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.015,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # Years 1, 2, 4, 5, 7 should have zero cost
    assert result[0] == 0.0
    assert result[1] == 0.0
    assert result[3] == 0.0
    assert result[4] == 0.0
    assert result[6] == 0.0


def test_boundary_exactly_at_replacement_interval(base_spec):
    """Test boundary: exactly at replacement interval (40k km)"""
    params = GlobalParams(
        years=4,
        km_per_year=10000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # Exactly 40k at year 4
    base_cost = 800.0 * 2.0
    assert abs(result[3] - base_cost) < 0.01
    
    # Years 1-3 should be 0
    assert result[0] == 0.0
    assert result[1] == 0.0
    assert result[2] == 0.0


def test_zero_years_edge_case(base_spec):
    """Test edge case: 0 years"""
    params = GlobalParams(
        years=0,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.015,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    assert len(result) == 0


def test_zero_km_per_year_edge_case(base_spec):
    """Test edge case: 0 km per year"""
    params = GlobalParams(
        years=8,
        km_per_year=0,
        discount_rate=0.04,
        energy_inflation=0.02,
        opex_inflation=0.015,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )
    
    result = tires_series(base_spec, params)
    
    # Should return all zeros
    assert len(result) == 8
    assert all(x == 0.0 for x in result)
