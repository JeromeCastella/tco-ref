# tco_core/energy.py
from __future__ import annotations
from typing import List, Tuple

def weighted_electricity_price(
    price_home: float,
    price_work: float,
    price_public: float,
    w_home: float,
    w_work: float,
    w_public: float,
) -> float:
    """
    Retourne le prix élec pondéré (CHF/kWh).
    - Les poids sont clampés dans [0,1], puis renormalisés pour sommer 1 si besoin.
    - Tolérance si la somme n'est pas exactement 1 (arrondis).
    """
    # clamp
    w_home = max(0.0, min(1.0, w_home))
    w_work = max(0.0, min(1.0, w_work))
    w_public = max(0.0, min(1.0, w_public))

    s = w_home + w_work + w_public
    if s <= 0:
        # fallback : tout à la maison si les poids sont tous nuls
        w_home, w_work, w_public = 1.0, 0.0, 0.0
        s = 1.0

    # renormalisation douce si ≠ 1 (ex: 0.999 à cause d'arrondis)
    if abs(s - 1.0) > 1e-9:
        w_home /= s
        w_work /= s
        w_public /= s

    return (price_home * w_home) + (price_work * w_work) + (price_public * w_public)


def make_inflation_series(start_value: float, annual_rate: float, years: int) -> List[float]:
    """
    Série avec croissance composée : [start, start*(1+r), ..., start*(1+r)^(years-1)].
    years >= 1.
    """
    if years < 1:
        return []
    series = []
    for t in range(years):
        series.append(start_value * ((1.0 + annual_rate) ** t))
    return series
