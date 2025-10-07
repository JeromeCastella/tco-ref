# tco_core/cashflows.py
from __future__ import annotations
from typing import List, Tuple, Any, Dict

from .models import Tech, GlobalParams, VehicleSpec
from .energy import weighted_electricity_price, make_inflation_series
from .tires import tires_series


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
    PHEV energy cost = mixed electric + thermal according to share_elec (0..1).
    
    The electric portion uses the WEIGHTED electricity price (same as BEV):
      weighted_price = w_home × price_home + w_work × price_work + w_public × price_public
    
    The thermal portion uses the standard fuel price.
    
    Formula:
      PHEV_cost = (km × share_elec × kwh_per_100/100 × elec_price_weighted) 
                + (km × (1-share_elec) × l_per_100/100 × fuel_price)
    
    Args:
        km: Annual distance (km)
        l_per_100: Fuel consumption (L/100km) for thermal portion
        kwh_per_100: Electric consumption (kWh/100km) for electric portion
        share_elec: Electric share (0.0 to 1.0), e.g., 0.5 = 50% electric, 50% thermal
        fuel_price_chf_per_l: Fuel price (CHF/L)
        elec_price_chf_per_kwh: WEIGHTED electricity price (CHF/kWh) from charging profile
    
    Returns:
        Total annual energy cost (CHF)
    """
    s_e = max(0.0, min(1.0, _as_float(share_elec)))
    energy_elec = annual_energy_cost_bev(_as_float(km) * s_e, kwh_per_100, elec_price_chf_per_kwh)
    energy_ice  = annual_energy_cost_ice(_as_float(km) * (1.0 - s_e), l_per_100, fuel_price_chf_per_l)
    return _as_float(energy_elec + energy_ice)


def build_energy_price_series(spec: VehicleSpec, params: GlobalParams, years: int) -> Tuple[List[float], List[float]]:
    """
    Build fuel and electricity price series (CHF/L and CHF/kWh) with energy inflation applied.
    
    The electricity price is WEIGHTED based on charging profile (home/work/public):
      weighted_elec_price = w_home × elec_price_home 
                          + w_work × elec_price_work 
                          + w_public × elec_price_public
    
    This weighted electricity price is used for:
      - BEV: 100% of energy consumption
      - PHEV: electric portion of energy consumption (share_elec × consumption)
    
    Both series are inflated year-over-year using the energy inflation rate.
    
    Args:
        spec: VehicleSpec with prices and charging weights (w_home, w_work, w_public)
        params: GlobalParams with energy_inflation rate
        years: Number of years for the series
    
    Returns:
        Tuple of (fuel_series, elec_series) - lists of prices for each year
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


# ---------- AUTRES COÛTS (BFE/EBP 2023 section 3.6) ----------

def other_costs_series(tech: Tech, spec: VehicleSpec, params: GlobalParams) -> List[float]:
    """
    Calcule la série des "autres coûts" annuels (BFE/EBP 2023 section 3.6).
    
    Structure annuelle :
    - Taxe cantonale (annual_tax_chf) : augmente avec opex_inflation
    - Assurance (annual_insurance_chf) : constante sur 8 ans
    - Soins du véhicule : params.vehicle_care_annual CHF/an, augmente avec opex_inflation
    - Infrastructure de recharge : params.charging_infrastructure CHF en année 1 pour BEV/PHEV uniquement (VR=0)
    
    Args:
        tech: Type de motorisation (ICE/BEV/PHEV)
        spec: Spécifications véhicule (taxe, assurance)
        params: Paramètres globaux (years, opex_inflation, vehicle_care_annual, charging_infrastructure)
    
    Returns:
        Liste des coûts annuels pour chaque année
    """
    tech_enum = _ensure_tech_enum(tech)
    years = int(params.years)
    opex_infl_mult = _inflation_multipliers(_as_float(params.opex_inflation), years)
    
    series = []
    for t in range(1, years + 1):
        # Taxe cantonale (avec inflation OPEX)
        tax = _as_float(spec.annual_tax_chf) * opex_infl_mult[t - 1]
        
        # Assurance (constante sur 8 ans)
        insurance = _as_float(spec.annual_insurance_chf)
        
        # Soins du véhicule (CHF/an avec inflation OPEX)
        care = _as_float(params.vehicle_care_annual) * opex_infl_mult[t - 1]
        
        # Infrastructure de recharge (année 1 pour BEV/PHEV, VR=0)
        infra = _as_float(params.charging_infrastructure) if (t == 1 and tech_enum in {Tech.BEV, Tech.PHEV}) else 0.0
        
        total = tax + insurance + care + infra
        series.append(total)
    
    return series


# ---------- LIGNE OPEX ANNUELLE ----------

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
        # part élec (uses WEIGHTED electricity price from charging profile)
        energy_elec = (float(spec.consumption_elec_kwh_per_100) / 100.0) * (float(km) * share_elec) * elec_price
        # part thermique (uses standard fuel price)
        energy_ice  = (float(spec.consumption_fuel_l_per_100)  / 100.0) * (float(km) * (1.0 - share_elec)) * fuel_price
        energy = energy_elec + energy_ice

    # --- MAINTENANCE & PNEUS ---
    maintenance = float(maint_ser[t - 1])
    tires       = float(tires_ser[t - 1])

    # --- AUTRES (BFE/EBP 2023 section 3.6) ---
    # Taxe cantonale (avec inflation OPEX)
    opex_infl = (1.0 + float(params.opex_inflation)) ** (t - 1)
    tax = float(spec.annual_tax_chf) * opex_infl
    
    # Assurance (constante sur 8 ans)
    insurance = float(spec.annual_insurance_chf)
    
    # Soins du véhicule (CHF/an avec inflation OPEX)
    care = float(params.vehicle_care_annual) * opex_infl
    
    # Infrastructure de recharge (année 1 pour BEV/PHEV, VR=0)
    infra = float(params.charging_infrastructure) if (t == 1 and tech in {Tech.BEV, Tech.PHEV}) else 0.0
    
    other = tax + insurance + care + infra

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
