# tco_core/cashflows.py
from __future__ import annotations
from typing import List, Tuple, Any

from .models import Tech, GlobalParams, VehicleSpec
from .energy import weighted_electricity_price, make_inflation_series


# ---------- helpers ----------

def _as_float(x: Any) -> float:
    """Defensive cast to float, raising a clear error if a placeholder (e.g., Ellipsis) slipped in."""
    if x is ...:
        raise TypeError("Found Ellipsis (...) where a number was expected. Check defaults/specs.")
    return float(x)


def _inflation_multipliers(rate: float, years: int) -> List[float]:
    """
    Adapter that works with either:
      - make_inflation_series(rate, years) -> [1, (1+r), (1+r)^2, ...]
      - or older custom signatures. If calling fails, we compute ourselves.
    """
    try:
        # Try modern signature (by position)
        res = make_inflation_series(rate, years)  # type: ignore[arg-type]
        # Must be a sequence of length `years`
        seq = list(res)
        if len(seq) == years:
            # If first elem is ~1.0 we consider it multipliers already; otherwise accept anyway.
            return [_as_float(v) for v in seq]
        # Fallback to computing ourselves
    except TypeError:
        pass
    # Safe fallback: we build multipliers ourselves
    r = _as_float(rate)
    return [(1.0 + r) ** t for t in range(years)]


def _ensure_tech_enum(tech: Any) -> Tech:
    """Coerce tech into Tech enum if it arrives as str/value."""
    if isinstance(tech, Tech):
        return tech
    # Try from value (string like "ICE"/"BEV"/"PHEV")
    try:
        return Tech(tech)  # e.g., Tech("ICE")
    except Exception:
        pass
    # Try from name (ICE/BEV/PHEV)
    if isinstance(tech, str):
        try:
            return Tech[tech]
        except Exception:
            pass
    raise TypeError(f"Invalid tech value: {tech!r} (expected Tech enum or valid string)")


# ---------- ÉNERGIE ----------

def annual_energy_cost_ice(km: float, l_per_100: float, fuel_price_chf_per_l: float) -> float:
    """ICE : (L/100km) * km * CHF/L"""
    return _as_float(( _as_float(l_per_100) / 100.0 ) * _as_float(km) * _as_float(fuel_price_chf_per_l))


def annual_energy_cost_bev(km: float, kwh_per_100: float, elec_price_chf_per_kwh: float) -> float:
    """BEV : (kWh/100km) * km * CHF/kWh"""
    return _as_float(( _as_float(kwh_per_100) / 100.0 ) * _as_float(km) * _as_float(elec_price_chf_per_kwh))


def annual_energy_cost_phev(
    km: float,
    l_per_100: float,
    kwh_per_100: float,
    share_elec: float,
    fuel_price_chf_per_l: float,
    elec_price_chf_per_kwh: float,
) -> float:
    """
    PHEV = mix élec + thermique selon share_elec (0..1).
    """
    s_e = max(0.0, min(1.0, _as_float(share_elec)))
    energy_elec = annual_energy_cost_bev(_as_float(km) * s_e, kwh_per_100, elec_price_chf_per_kwh)
    energy_ice  = annual_energy_cost_ice(_as_float(km) * (1.0 - s_e), l_per_100, fuel_price_chf_per_l)
    return _as_float(energy_elec + energy_ice)


def build_energy_price_series(spec: VehicleSpec, params: GlobalParams, years: int) -> Tuple[List[float], List[float]]:
    """
    Retourne (fuel_series, elec_series) en CHF/L et CHF/kWh, avec inflation énergie appliquée.
    """
    infl = _inflation_multipliers(_as_float(params.energy_inflation), years)

    # Carburant
    fuel0 = _as_float(spec.fuel_price_chf_per_l)
    fuel_series = [_as_float(fuel0 * infl[t]) for t in range(years)]

    # Électricité pondérée base
    elec_base = _as_float(weighted_electricity_price(
        _as_float(spec.elec_price_home), _as_float(spec.elec_price_work), _as_float(spec.elec_price_public),
        _as_float(spec.w_home), _as_float(spec.w_work), _as_float(spec.w_public)
    ))
    elec_series = [_as_float(elec_base * infl[t]) for t in range(years)]

    return fuel_series, elec_series


# ---------- MAINTENANCE & PNEUS (MVP méthodo) ----------

def maintenance_series(spec: VehicleSpec, params: GlobalParams, years: int) -> List[float]:
    """
    Règle 7/6 → 8 ans (simple) + inflation OPEX.
    """
    if years <= 0:
        return []

    base_annual = _as_float(spec.maint_6y_chf) / 6.0
    r_opex = _as_float(params.opex_inflation)

    out: List[float] = []
    for t in range(1, years + 1):
        annual = base_annual
        if params.apply_maint_7_over_6 and t > 6:
            annual *= (7.0 / 6.0)
        annual *= (1.0 + r_opex) ** (t - 1)
        out.append(_as_float(annual))
    return out


def tires_series(spec: VehicleSpec, params: GlobalParams, years: int) -> List[float]:
    """
    Pneu base (×2 si coché), lissé par an + inflation OPEX.
    """
    if years <= 0:
        return []
    total = _as_float(spec.tires_base_chf) * (2.0 if params.include_tires_x2 else 1.0)
    base_annual = total / _as_float(years)
    r_opex = _as_float(params.opex_inflation)
    return [_as_float(base_annual * ((1.0 + r_opex) ** (t - 1))) for t in range(1, years + 1)]


# ---------- LIGNE OPEX ANNUELLE ----------

# tco_core/cashflows.py  — remplace ENTIEREMENT annual_opex_row par ceci
from typing import Dict

def annual_opex_row(
    tech,
    year_index_1based: int,
    km: float,
    spec,
    params,
    fuel_series,
    elec_series,
    maint_ser,
    tires_ser,
) -> Dict[str, float]:
    """
    Calcule les OPEX pour l'année t (1..years) et renvoie un dict avec:
      energy, maintenance, tires, other, opex_total, cashflow
    - energy dépend de la techno (ICE/BEV/PHEV) et des séries de prix (déjà inflationnées)
    - maintenance / tires viennent des séries correspondantes (déjà inflationnées)
    - other = 0.0 (placeholder, extensible plus tard)
    - cashflow = -opex_total  (coût -> flux négatif)
    """
    t = year_index_1based
    # --- ÉNERGIE ---
    if tech == Tech.ICE:
        price = float(fuel_series[t - 1])
        energy = (float(spec.consumption_fuel_l_per_100) / 100.0) * float(km) * price

    elif tech == Tech.BEV:
        price = float(elec_series[t - 1])
        energy = (float(spec.consumption_elec_kwh_per_100) / 100.0) * float(km) * price

    else:  # Tech.PHEV
        fuel_price = float(fuel_series[t - 1])
        elec_price = float(elec_series[t - 1])
        share_elec = max(0.0, min(1.0, float(spec.phev_share_elec)))
        # part élec
        energy_elec = (float(spec.consumption_elec_kwh_per_100) / 100.0) * (float(km) * share_elec) * elec_price
        # part thermique
        energy_ice  = (float(spec.consumption_fuel_l_per_100)  / 100.0) * (float(km) * (1.0 - share_elec)) * fuel_price
        energy = energy_elec + energy_ice

    # --- MAINTENANCE & PNEUS ---
    maintenance = float(maint_ser[t - 1])
    tires       = float(tires_ser[t - 1])

    # --- AUTRES (placeholder) ---
    other = 0.0

    # --- TOTAUX ---
    opex_total = float(energy + maintenance + tires + other)
    cashflow   = float(-opex_total)

    return {
        "energy":      energy,
        "maintenance": maintenance,
        "tires":       tires,
        "other":       other,
        "opex_total":  opex_total,
        "cashflow":    cashflow,
    }
