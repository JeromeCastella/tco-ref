# tco_core/validation.py
from __future__ import annotations
from typing import Tuple, Dict
from .models import GlobalParams, Results, Tech

def capex_net_and_opex_discounted(res: Results, params: GlobalParams) -> Tuple[float, float]:
    """
    Retourne (capex_net, opex_actualises) pour un Results donné.
    - capex_net = prix d'achat - VR actualisée
    - opex_actualises = somme des OPEX / (1+r)^t à partir de la table annuelle
    Hypothèse: annual_table contient colonnes:
      'Année', 'OPEX total', et la VR est déjà incluse dans le cashflow de la dernière année.
    """
    purchase = res.annual_table.attrs.get("purchase_price", None)
    residual_nominal = res.residual_value_nominal
    years = int(res.annual_table["Année"].max())

    # CAPEX net = achat - VR actualisée
    vr_disc = residual_nominal / ((1.0 + params.discount_rate) ** years)
    capex_net = float(purchase - vr_disc) if purchase is not None else float("nan")

    # OPEX actualisés (on re-disconte les OPEX annuels)
    opex_disc = float((res.annual_table["OPEX total"] / ((1.0 + params.discount_rate) ** res.annual_table["Année"])).sum())
    return capex_net, opex_disc


def check_decomposition(res: Results, params: GlobalParams, tol: float = 1e-2) -> Tuple[bool, float, float, float]:
    """
    Vérifie |NPV| ≈ CAPEX_net + OPEX_actualisés.
    Retourne (ok, abs_npv, capex_net, opex_disc).
    """
    capex_net, opex_disc = capex_net_and_opex_discounted(res, params)
    abs_npv = abs(res.npv_total)
    ok = abs(abs_npv - (capex_net + opex_disc)) <= tol
    return ok, abs_npv, capex_net, opex_disc
