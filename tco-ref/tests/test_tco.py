# tests/test_tco.py
from tco_core.models import Tech, GlobalParams, VehicleSpec
from tco_core.tco import compute_tco_vehicle

def _params_simple():
    return GlobalParams(
        years=2,
        km_per_year=10_000,
        discount_rate=0.0,    # pour un test simple sans actualisation
        energy_inflation=0.0,
        opex_inflation=0.0,
        include_tires_x2=False,
        apply_maint_7_over_6=False,
        vehicle_care_annual=0.0,
        charging_infrastructure=0.0,
    )

def _spec_bev_simple():
    return VehicleSpec(
        tech=Tech.BEV,
        vehicle_class="midsize",
        purchase_price=40_000.0,
        residual_rate_8y_hint=0.30,  # sur 2 ans ici, on laisse tel quel pour le test
        consumption_fuel_l_per_100=0.0,
        consumption_elec_kwh_per_100=15.0,
        fuel_price_chf_per_l=2.0,
        elec_price_home=0.20,
        elec_price_work=0.20,
        elec_price_public=0.50,
        w_home=1.0, w_work=0.0, w_public=0.0,  # tout à la maison = 0.20
        maint_6y_chf=0.0,
        tires_base_chf=0.0,
        annual_tax_chf=0.0,
        annual_insurance_chf=0.0,
        phev_share_elec=1.0,
    )

def test_tco_bev_simple_no_inflation_no_opex():
    p = _params_simple()
    s = _spec_bev_simple()
    res = compute_tco_vehicle(p, s)
    # Cashflows: année 0 -40'000 ; année 1 coût élec ; année 2 coût élec + VR
    # prix elec = 0.20 ; conso = 15kWh/100 ; 10'000km -> 1500kWh -> 300 CHF/an
    # VR with BFE/EBP 2023 (corrected):
    #   VR_6 = 40'000 × 0.30 = 12'000 (NO 0.9 adjustment at year 6)
    #   VR_2 = 40'000 - (40'000 - 12'000) × (2/6) = 30'666.67
    # NPV = -40'000 - 300 + (30'666.67 - 300) = -9'933.33
    expected_npv = -9_933.333333333334
    assert abs(res.npv_total - expected_npv) < 0.01
    # TCO/km = |NPV| / 20'000 km
    assert abs(res.tco_per_km - (abs(expected_npv) / 20_000.0)) < 1e-6
