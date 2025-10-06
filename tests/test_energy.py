# tests/test_energy.py
from tco_core.energy import weighted_electricity_price, make_inflation_series

def test_weighted_electricity_price_basic():
    # 90% maison (0.2), 0% travail (0.2), 10% public (0.5) -> 0.23
    p = weighted_electricity_price(0.2, 0.2, 0.5, 0.9, 0.0, 0.1)
    assert abs(p - 0.23) < 1e-9

def test_weighted_electricity_price_renormalize():
    # Somme 0.85 -> renormalise à 1
    p = weighted_electricity_price(0.2, 0.4, 0.6, 0.5, 0.3, 0.05)  # somme 0.85
    # calcul manuel renormalisé
    wh, ww, wp = 0.5/0.85, 0.3/0.85, 0.05/0.85
    expected = 0.2*wh + 0.4*ww + 0.6*wp
    assert abs(p - expected) < 1e-12

def test_weighted_electricity_price_all_zero_weights():
    # Tous poids 0 -> fallback maison = 1
    p = weighted_electricity_price(0.25, 0.50, 0.75, 0.0, 0.0, 0.0)
    assert abs(p - 0.25) < 1e-12

def test_make_inflation_series():
    s = make_inflation_series(100.0, 0.1, 5)
    # 100, 110, 121, 133.1, 146.41
    assert len(s) == 5
    assert abs(s[0] - 100.0) < 1e-12
    assert abs(s[1] - 110.0) < 1e-12
    assert abs(s[4] - 146.41) < 1e-9
