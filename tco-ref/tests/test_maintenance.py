# tests/test_maintenance.py
from tco_core.maintenance import maintenance_series
from tco_core.models import GlobalParams, VehicleSpec, Tech


def test_6_year_sum_without_inflation():
    """Test that sum of first 6 years equals maint_6y_chf when inflation is 0"""
    spec = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=6,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=False,
    )
    
    series = maintenance_series(spec, params)
    total = sum(series)
    
    assert len(series) == 6
    assert abs(total - 6000.0) < 1e-9


def test_6_year_sum_with_inflation():
    """Test that base costs (before inflation) sum to maint_6y_chf"""
    spec = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=6,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.05,
        apply_maint_7_over_6=False,
    )
    
    series = maintenance_series(spec, params)
    # Base cost per year is 1000
    # With 5% inflation: year 1: 1000, year 2: 1050, year 3: 1102.5, etc.
    assert len(series) == 6
    assert abs(series[0] - 1000.0) < 1e-9
    assert abs(series[1] - 1050.0) < 1e-9
    assert abs(series[2] - 1102.5) < 1e-9


def test_7_over_6_adjustment_year_7():
    """Test that year 7 applies 7/6 multiplier when flag is True"""
    spec = VehicleSpec(
        tech=Tech.BEV,
        vehicle_class="compact",
        purchase_price=35000.0,
        residual_rate_8y_hint=0.40,
        consumption_fuel_l_per_100=0.0,
        consumption_elec_kwh_per_100=17.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
    )
    
    series = maintenance_series(spec, params)
    base_annual = 6000.0 / 6.0  # 1000.0
    
    # Years 1-6: base_annual
    for i in range(6):
        assert abs(series[i] - base_annual) < 1e-9
    
    # Years 7-8: base_annual * 7/6
    expected_7_8 = base_annual * (7.0 / 6.0)
    assert abs(series[6] - expected_7_8) < 1e-9
    assert abs(series[7] - expected_7_8) < 1e-9


def test_7_over_6_flag_disabled():
    """Test that 7/6 adjustment is NOT applied when flag is False"""
    spec = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="midsize",
        purchase_price=40000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=7.0,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=False,
    )
    
    series = maintenance_series(spec, params)
    base_annual = 6000.0 / 6.0  # 1000.0
    
    # All years should be base_annual (no 7/6 adjustment)
    for cost in series:
        assert abs(cost - base_annual) < 1e-9


def test_inflation_compounding():
    """Test that OPEX inflation compounds correctly year over year"""
    spec = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=5,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.1,  # 10% inflation
        apply_maint_7_over_6=False,
    )
    
    series = maintenance_series(spec, params)
    base_annual = 6000.0 / 6.0  # 1000.0
    
    # Year 1: 1000 * 1.1^0 = 1000
    # Year 2: 1000 * 1.1^1 = 1100
    # Year 3: 1000 * 1.1^2 = 1210
    # Year 4: 1000 * 1.1^3 = 1331
    # Year 5: 1000 * 1.1^4 = 1464.1
    assert abs(series[0] - 1000.0) < 1e-9
    assert abs(series[1] - 1100.0) < 1e-9
    assert abs(series[2] - 1210.0) < 1e-9
    assert abs(series[3] - 1331.0) < 1e-9
    assert abs(series[4] - 1464.1) < 1e-9


def test_combined_7_over_6_and_inflation():
    """Test combination of 7/6 adjustment and inflation"""
    spec = VehicleSpec(
        tech=Tech.PHEV,
        vehicle_class="suv",
        purchase_price=50000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=5.0,
        consumption_elec_kwh_per_100=18.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.7,
        w_work=0.2,
        w_public=0.1,
        maint_6y_chf=7200.0,
        tires_base_chf=1000.0,
        phev_share_elec=0.6,
    )
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.03,  # 3% inflation
        apply_maint_7_over_6=True,
    )
    
    series = maintenance_series(spec, params)
    base_annual = 7200.0 / 6.0  # 1200.0
    
    # Year 6 (index 5): 1200 * 1.03^5 = 1200 * 1.159274... ≈ 1391.13
    expected_year_6 = base_annual * (1.03 ** 5)
    assert abs(series[5] - expected_year_6) < 1e-2
    
    # Year 7 (index 6): 1200 * (7/6) * 1.03^6 = 1400 * 1.194052... ≈ 1671.67
    expected_year_7 = base_annual * (7.0 / 6.0) * (1.03 ** 6)
    assert abs(series[6] - expected_year_7) < 1e-2
    
    # Year 8 (index 7): 1200 * (7/6) * 1.03^7 = 1400 * 1.229873... ≈ 1721.82
    expected_year_8 = base_annual * (7.0 / 6.0) * (1.03 ** 7)
    assert abs(series[7] - expected_year_8) < 1e-2


def test_edge_case_3_years():
    """Test with horizon shorter than 6 years (3 years)"""
    spec = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=3,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
    )
    
    series = maintenance_series(spec, params)
    base_annual = 6000.0 / 6.0  # 1000.0
    
    assert len(series) == 3
    # All years should be base_annual (no 7/6 since all years <= 6)
    for cost in series:
        assert abs(cost - base_annual) < 1e-9


def test_edge_case_15_years():
    """Test with long horizon (15 years)"""
    spec = VehicleSpec(
        tech=Tech.BEV,
        vehicle_class="midsize",
        purchase_price=40000.0,
        residual_rate_8y_hint=0.40,
        consumption_fuel_l_per_100=0.0,
        consumption_elec_kwh_per_100=16.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=15,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
    )
    
    series = maintenance_series(spec, params)
    base_annual = 6000.0 / 6.0  # 1000.0
    expected_7_plus = base_annual * (7.0 / 6.0)
    
    assert len(series) == 15
    # Years 1-6: base_annual
    for i in range(6):
        assert abs(series[i] - base_annual) < 1e-9
    # Years 7-15: 7/6 adjustment
    for i in range(6, 15):
        assert abs(series[i] - expected_7_plus) < 1e-9


def test_exactly_6_years():
    """Test edge case with exactly 6 years (boundary condition)"""
    spec = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=6,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
    )
    
    series = maintenance_series(spec, params)
    base_annual = 6000.0 / 6.0  # 1000.0
    
    assert len(series) == 6
    # All 6 years should be base_annual (no year 7+)
    for cost in series:
        assert abs(cost - base_annual) < 1e-9


def test_zero_years():
    """Test edge case with 0 years (should return empty list)"""
    spec = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    params = GlobalParams(
        years=0,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
    )
    
    series = maintenance_series(spec, params)
    assert series == []


def test_different_maint_costs():
    """Test that different maint_6y_chf values produce proportional results"""
    spec1 = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="compact",
        purchase_price=30000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=6.5,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=6000.0,
        tires_base_chf=800.0,
    )
    spec2 = VehicleSpec(
        tech=Tech.ICE,
        vehicle_class="suv",
        purchase_price=50000.0,
        residual_rate_8y_hint=0.35,
        consumption_fuel_l_per_100=8.0,
        consumption_elec_kwh_per_100=0.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.2,
        elec_price_work=0.2,
        elec_price_public=0.5,
        w_home=0.9,
        w_work=0.0,
        w_public=0.1,
        maint_6y_chf=9000.0,  # 1.5x more expensive
        tires_base_chf=1000.0,
    )
    params = GlobalParams(
        years=8,
        km_per_year=15000,
        discount_rate=0.04,
        energy_inflation=0.0,
        opex_inflation=0.0,
        apply_maint_7_over_6=True,
    )
    
    series1 = maintenance_series(spec1, params)
    series2 = maintenance_series(spec2, params)
    
    # Each year in series2 should be 1.5x series1
    for i in range(len(series1)):
        assert abs(series2[i] - series1[i] * 1.5) < 1e-9
