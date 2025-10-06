from __future__ import annotations
from typing import List
from .models import GlobalParams, VehicleSpec

def maintenance_series(params: GlobalParams, spec: VehicleSpec) -> List[float]:
    """
    Série annuelle de maintenance (CHF, nominal) avec inflation OPEX.
    Hypothèse MVP (méthodo 7/6 simplifiée) :
      - coût par an constant = maint_6y_chf / 6
      - extrapolation 7..N ans => même coût annuel
      - inflation OPEX appliquée chaque année (composition)
    """
    years = int(params.years)
    base_per_year = spec.maint_6y_chf / 6.0  # CHF/an
    # montant nominal année t = base * (1+infl)^t-1  (t=1 -> facteur 1)
    return [base_per_year * ((1.0 + params.opex_inflation) ** (t-1)) for t in range(1, years+1)]
