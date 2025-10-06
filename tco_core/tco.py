from __future__ import annotations
from typing import Dict, List
import math
import pandas as pd

from .models import Tech, GlobalParams, VehicleSpec, Results
from .cashflows import (
    build_energy_price_series,
    annual_opex_row,
)
from .maintenance import maintenance_series
from .residual import residual_at_end
from .tires import tires_series

def _npv(cashflows: List[float], r: float) -> float:
    if r == 0.0:
        return float(sum(cashflows))
    return float(sum(cf / ((1.0 + r) ** t) for t, cf in enumerate(cashflows)))

def compute_tco_vehicle(params: GlobalParams, spec: VehicleSpec) -> Results:
    years = params.years
    km_per_year = params.km_per_year

    # Séries de prix / opex
    fuel_ser, elec_ser = build_energy_price_series(spec, params, years)
    maint_ser = maintenance_series(spec, params)
    tires_ser = tires_series(spec, params)

    # Flux année 0 : achat
    cashflows = [-spec.purchase_price]
    rows = []

    total_km = km_per_year * years

    # Flux annuels d’exploitation
    for t in range(1, years + 1):
        opex = annual_opex_row(
            tech=spec.tech,
            year_index_1based=t,
            km=km_per_year,
            spec=spec,
            params=params,
            fuel_series=fuel_ser,
            elec_series=elec_ser,
            maint_ser=maint_ser,
            tires_ser=tires_ser,
        )
        rows.append({
            "Année": t,
            "km": km_per_year,
            "Énergie": opex["energy"],
            "Maintenance": opex["maintenance"],
            "Pneus": opex["tires"],
            "Autres": opex["other"],           # <- colonne standardisée
            "OPEX total": opex["opex_total"],
            "Cashflow": opex["cashflow"],
        })
        cashflows.append(opex["cashflow"])

    # Valeur résiduelle (nominale) ajoutée l’année finale
    # Valeur résiduelle avec méthodologie BFE/EBP 2023
    residual_nominal, residual_discounted = residual_at_end(spec, years, params)
    cashflows[-1] += residual_nominal
    rows[-1]["Valeur résiduelle (nominale)"] = residual_nominal
    rows[-1]["Cashflow"] += residual_nominal

    # Table + actualisation
    df = pd.DataFrame(rows)
    df["Cashflow actualisé"] = [
        cf / ((1.0 + params.discount_rate) ** t) for t, cf in enumerate(cashflows[1:], start=1)
    ]
    df["Cumul NPV"] = df["Cashflow actualisé"].cumsum() + cashflows[0]

    # Pour les graphes/décompositions
    df.attrs["purchase_price"] = spec.purchase_price
    df.attrs["tech"] = spec.tech.value
    df.attrs["vehicle_class"] = spec.vehicle_class

    # NPV & TCO
    npv_total = _npv(cashflows, params.discount_rate)
    tco_per_km = abs(npv_total) / total_km if total_km > 0 else math.inf

    return Results(
        tech=spec.tech,
        vehicle_class=spec.vehicle_class,
        npv_total=npv_total,
        tco_per_km=tco_per_km,
        residual_value_nominal=residual_nominal,
        residual_value_discounted=residual_discounted,
        annual_table=df,
    )

def compute_all_techs(params: GlobalParams, specs_by_tech: Dict[Tech, VehicleSpec]) -> Dict[Tech, Results]:
    return {tech: compute_tco_vehicle(params, spec) for tech, spec in specs_by_tech.items()}
