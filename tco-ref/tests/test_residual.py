import pytest
from tco_core.models import Tech, GlobalParams, VehicleSpec
from tco_core.residual import residual_at_end


def _params(years=8, discount_rate=0.04):
    """Helper to create GlobalParams for testing."""
    return GlobalParams(
        years=years,
        km_per_year=15_000,
        discount_rate=discount_rate,
        energy_inflation=0.02,
        opex_inflation=0.015,
        apply_maint_7_over_6=True,
        include_tires_x2=True,
    )


def _spec(purchase_price=50_000, residual_rate_8y_hint=0.35):
    """Helper to create VehicleSpec for testing."""
    return VehicleSpec(
        tech=Tech.BEV,
        vehicle_class="midsize",
        purchase_price=purchase_price,
        residual_rate_8y_hint=residual_rate_8y_hint,
        consumption_fuel_l_per_100=0.0,
        consumption_elec_kwh_per_100=17.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.20,
        elec_price_work=0.25,
        elec_price_public=0.50,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=1700,
        tires_base_chf=1000,
        phev_share_elec=1.0,
    )


def test_residual_at_6_years():
    """Test residual value at exactly 6 years with BFE/EBP 2023 methodology."""
    spec = _spec(purchase_price=50_000, residual_rate_8y_hint=0.35)
    params = _params(years=6, discount_rate=0.04)
    
    vr_nom, vr_disc = residual_at_end(spec, 6, params)
    
    # At 6 years: VR = 50_000 × 0.35 = 17_500 (NO 0.9 adjustment)
    expected_nominal = 50_000 * 0.35
    assert abs(vr_nom - expected_nominal) < 0.01, f"Expected {expected_nominal}, got {vr_nom}"
    
    # Discounted: 17_500 / (1.04^6)
    expected_discounted = expected_nominal / (1.04 ** 6)
    assert abs(vr_disc - expected_discounted) < 0.01


def test_residual_at_8_years():
    """Test residual value at 8 years with geometric extrapolation."""
    spec = _spec(purchase_price=50_000, residual_rate_8y_hint=0.35)
    params = _params(years=8, discount_rate=0.04)
    
    vr_nom, vr_disc = residual_at_end(spec, 8, params)
    
    # VR_6 = 50_000 × 0.35 = 17_500
    # VR_8 = VR_6 × 0.9 = 17_500 × 0.9 = 15_750
    vr_6 = 50_000 * 0.35
    expected_nominal = vr_6 * 0.9
    
    assert abs(vr_nom - expected_nominal) < 0.01, f"Expected {expected_nominal}, got {vr_nom}"
    
    # Discounted
    expected_discounted = expected_nominal / (1.04 ** 8)
    assert abs(vr_disc - expected_discounted) < 0.01


def test_residual_at_3_years():
    """Test residual value at 3 years with linear interpolation."""
    spec = _spec(purchase_price=50_000, residual_rate_8y_hint=0.35)
    params = _params(years=3, discount_rate=0.04)
    
    vr_nom, vr_disc = residual_at_end(spec, 3, params)
    
    # VR_6 = 50_000 × 0.35 = 17_500 (NO 0.9 adjustment)
    # Linear interpolation: VR_3 = 50_000 - (50_000 - 17_500) × (3/6)
    vr_6 = 50_000 * 0.35
    depreciation_to_6 = 50_000 - vr_6
    expected_nominal = 50_000 - (depreciation_to_6 * (3.0 / 6.0))
    
    assert abs(vr_nom - expected_nominal) < 0.01
    
    # Discounted
    expected_discounted = expected_nominal / (1.04 ** 3)
    assert abs(vr_disc - expected_discounted) < 0.01


def test_residual_at_1_year():
    """Test residual value at 1 year - edge case."""
    spec = _spec(purchase_price=40_000, residual_rate_8y_hint=0.30)
    params = _params(years=1, discount_rate=0.05)
    
    vr_nom, vr_disc = residual_at_end(spec, 1, params)
    
    # VR_6 = 40_000 × 0.30 = 12_000 (NO 0.9 adjustment)
    # Linear: VR_1 = 40_000 - (40_000 - 12_000) × (1/6)
    vr_6 = 40_000 * 0.30
    expected_nominal = 40_000 - ((40_000 - vr_6) * (1.0 / 6.0))
    
    assert abs(vr_nom - expected_nominal) < 0.01
    assert vr_nom < 40_000  # Should be less than purchase price


def test_residual_at_15_years():
    """Test residual value at 15 years - long term extrapolation."""
    spec = _spec(purchase_price=60_000, residual_rate_8y_hint=0.40)
    params = _params(years=15, discount_rate=0.03)
    
    vr_nom, vr_disc = residual_at_end(spec, 15, params)
    
    # VR_6 = 60_000 × 0.40 = 24_000 (NO 0.9 adjustment)
    # For years > 6: VR(t) = VR_6 × 0.9^((t-6)/2)
    # VR_15 = 24_000 × 0.9^((15-6)/2) = 24_000 × 0.9^4.5
    vr_6 = 60_000 * 0.40
    years_beyond_6 = 15 - 6
    expected_nominal = vr_6 * (0.9 ** (years_beyond_6 / 2.0))
    
    assert abs(vr_nom - expected_nominal) < 0.01
    assert vr_nom > 0  # Should still have some value
    assert vr_nom < vr_6  # Should be less than 6-year value


def test_residual_with_zero_discount_rate():
    """Test that with zero discount rate, nominal equals discounted."""
    spec = _spec(purchase_price=45_000, residual_rate_8y_hint=0.32)
    params = _params(years=8, discount_rate=0.0)
    
    vr_nom, vr_disc = residual_at_end(spec, 8, params)
    
    assert abs(vr_nom - vr_disc) < 0.01


def test_residual_with_high_discount_rate():
    """Test residual value with high discount rate."""
    spec = _spec(purchase_price=50_000, residual_rate_8y_hint=0.35)
    params = _params(years=8, discount_rate=0.10)
    
    vr_nom, vr_disc = residual_at_end(spec, 8, params)
    
    # VR_discounted should be significantly less than VR_nominal
    assert vr_disc < vr_nom
    expected_discounted = vr_nom / (1.10 ** 8)
    assert abs(vr_disc - expected_discounted) < 0.01


def test_residual_nominal_discounted_relationship():
    """Test that VR_discounted is always correctly related to VR_nominal."""
    spec = _spec(purchase_price=55_000, residual_rate_8y_hint=0.38)
    
    for years in [1, 3, 6, 8, 10, 15]:
        params = _params(years=years, discount_rate=0.04)
        vr_nom, vr_disc = residual_at_end(spec, years, params)
        
        # Calculate expected discounted value
        expected_disc = vr_nom / ((1.04) ** years)
        assert abs(vr_disc - expected_disc) < 0.01, f"Failed at year {years}"


def test_residual_non_negative():
    """Test that residual value is never negative."""
    spec = _spec(purchase_price=30_000, residual_rate_8y_hint=0.20)
    
    for years in [1, 5, 10, 20, 30]:
        params = _params(years=years, discount_rate=0.05)
        vr_nom, vr_disc = residual_at_end(spec, years, params)
        
        assert vr_nom >= 0, f"Nominal VR negative at year {years}"
        assert vr_disc >= 0, f"Discounted VR negative at year {years}"


def test_residual_never_exceeds_purchase_price():
    """Test that residual value never exceeds purchase price."""
    spec = _spec(purchase_price=70_000, residual_rate_8y_hint=0.45)
    
    for years in [1, 2, 3, 4, 5, 6, 8, 10]:
        params = _params(years=years, discount_rate=0.03)
        vr_nom, vr_disc = residual_at_end(spec, years, params)
        
        assert vr_nom <= 70_000, f"Nominal VR exceeds purchase at year {years}"


def test_residual_with_different_hints():
    """Test residual calculation with different hint values."""
    purchase_price = 50_000
    params = _params(years=6, discount_rate=0.04)
    
    hints = [0.20, 0.30, 0.40, 0.50]
    
    for hint in hints:
        spec = _spec(purchase_price=purchase_price, residual_rate_8y_hint=hint)
        vr_nom, vr_disc = residual_at_end(spec, 6, params)
        
        # At 6 years: VR = purchase_price × hint (NO 0.9 adjustment)
        expected = purchase_price * hint
        assert abs(vr_nom - expected) < 0.01


def test_residual_invalid_method():
    """Test that invalid method raises ValueError."""
    spec = _spec()
    params = _params()
    
    with pytest.raises(ValueError, match="Unsupported method"):
        residual_at_end(spec, 8, params, method="invalid_method")


def test_residual_bfe_2023_ten_percent_adjustment():
    """Test that the -10% adjustment is correctly applied from year 6 to year 8."""
    spec = _spec(purchase_price=100_000, residual_rate_8y_hint=0.40)
    
    # Test at year 6: NO adjustment
    params_6 = _params(years=6, discount_rate=0.0)
    vr_nom_6, vr_disc_6 = residual_at_end(spec, 6, params_6)
    
    # At year 6: VR = 100_000 × 0.40 = 40_000 (NO 0.9 adjustment)
    assert abs(vr_nom_6 - 40_000) < 0.01
    
    # Test at year 8: WITH 10% reduction
    params_8 = _params(years=8, discount_rate=0.0)
    vr_nom_8, vr_disc_8 = residual_at_end(spec, 8, params_8)
    
    # At year 8: VR = 40_000 × 0.9 = 36_000
    assert abs(vr_nom_8 - 36_000) < 0.01
    
    # Verify the 10% reduction from year 6 to year 8
    assert abs(vr_nom_8 - (vr_nom_6 * 0.9)) < 0.01
