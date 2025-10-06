from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

import pandas as pd



class Tech(Enum):
    ICE = "ICE"
    BEV = "BEV"
    PHEV = "PHEV"


@dataclass
class GlobalParams:
    years: int                 # horizon (années)
    km_per_year: int           # km/an (moyenne simple pour MVP)
    discount_rate: float       # r (décimal, ex. 0.04)
    energy_inflation: float    # inflation énergie (décimal)
    opex_inflation: float      # inflation OPEX (décimal)

    # Règles méthodo (on les branchera plus tard)
    apply_maint_7_over_6: bool = True
    include_tires_x2: bool = True


@dataclass
class VehicleSpec:
    tech: Tech
    vehicle_class: str                 # ex: "compact", "midsize", "suv"

    # CAPEX / VR
    purchase_price: float              # CHF
    residual_rate_8y: float            # fraction du prix, ex 0.35

    # Consommations
    consumption_fuel_l_per_100: float      # ICE/PHEV (L/100km)
    consumption_elec_kwh_per_100: float    # BEV/PHEV (kWh/100km)

    # Énergie — prix de base
    fuel_price_chf_per_l: float        # CHF/L
    elec_price_home: float             # CHF/kWh
    elec_price_work: float             # CHF/kWh
    elec_price_public: float           # CHF/kWh

    # Profil de recharge (somme=1) — utilisé pour BEV/PHEV
    w_home: float                      # ex 0.9
    w_work: float                      # ex 0.0
    w_public: float                    # ex 0.1

    # Maintenance & pneus — bases (on raffinera)
    maint_6y_chf: float                # coût cumulé sur 6 ans (méthodo)
    tires_base_chf: float              # coût total pneus (base)

    # PHEV : part de km roulés en élec (laisser un défaut pour ICE/BEV)
    phev_share_elec: float = 0.5       # ∈ [0,1] ; part carburant = 1 - part élec


@dataclass
class TCOResult:
    tech: Tech
    vehicle_class: str
    npv_total: float
    tco_per_km: float
    residual_value_nominal: float
    annual_table: "pandas.DataFrame"   # type forward reference pour éviter l’import pandas ici



@dataclass
class Results:
    tech: "Tech"
    vehicle_class: str
    npv_total: float
    tco_per_km: float
    residual_value_nominal: float
    annual_table: pd.DataFrame
