from __future__ import annotations
from typing import List
from .models import GlobalParams, VehicleSpec

def tires_series(params: GlobalParams, spec: VehicleSpec) -> List[float]:
    """
    Série annuelle pneus (CHF, nominal) avec inflation OPEX.
    MVP :
      - total pneus = tires_base_chf * (2 si include_tires_x2 sinon 1)
      - répartition uniforme / an puis inflation OPEX composée.
    """
    years = int(params.years)
    factor = 2.0 if params.include_tires_x2 else 1.0
    total = spec.tires_base_chf * factor
    per_year0 = total / years if years > 0 else 0.0
    return [per_year0 * ((1.0 + params.opex_inflation) ** (t-1)) for t in range(1, years+1)]
