from __future__ import annotations
from typing import List
from .models import GlobalParams, VehicleSpec

def maintenance_series(spec: VehicleSpec, params: GlobalParams) -> List[float]:
    """
    Série annuelle de maintenance (CHF, nominal) avec méthodologie BFE/EBP 2023.
    
    La règle 7/6 → 8 ans stipule que :
      - Le coût cumulé sur 6 ans est donné par spec.maint_6y_chf
      - Pour les années 1-6 : coût de base annuel = maint_6y_chf / 6
      - Pour les années 7+ : application du facteur 7/6 si apply_maint_7_over_6 est activé
      - L'inflation OPEX est appliquée chaque année : coût_t = coût_base × (1 + r_opex)^(t-1)
    
    Args:
        spec: Spécifications du véhicule (contient maint_6y_chf)
        params: Paramètres globaux (contient years, opex_inflation, apply_maint_7_over_6)
    
    Returns:
        Liste des coûts annuels de maintenance (CHF, nominal) pour chaque année
    """
    years = int(params.years)
    if years <= 0:
        return []
    
    base_annual = spec.maint_6y_chf / 6.0
    r_opex = params.opex_inflation
    
    result: List[float] = []
    for t in range(1, years + 1):
        annual = base_annual
        if params.apply_maint_7_over_6 and t > 6:
            annual *= (7.0 / 6.0)
        annual *= (1.0 + r_opex) ** (t - 1)
        result.append(annual)
    
    return result
