from __future__ import annotations
# --- hack chemin local (à retirer quand on packagera) ---
import sys, os
sys.path.append(os.path.dirname(__file__))
# --------------------------------------------------------

import streamlit as st
import pandas as pd

from tco_core.models import Tech, GlobalParams, VehicleSpec
from tco_core.tco import compute_all_techs

from charts import (
    make_decomposition_df_by_post,
    fig_bar_decomposition_by_post,
    make_cum_df,
    fig_line_cumulative,
)


# ======================== Helpers / Specs ========================

def make_spec(tech: Tech) -> VehicleSpec:
    """Placeholders homogènes pour démarrer (on branchera les defaults par classe ensuite)."""
    return VehicleSpec(
        tech=tech,
        vehicle_class="midsize",
        purchase_price=50_000.0,
        residual_rate_8y=0.30,
        consumption_fuel_l_per_100=6.5 if tech != Tech.BEV else 0.0,
        consumption_elec_kwh_per_100=17.0 if tech != Tech.ICE else 0.0,
        fuel_price_chf_per_l=2.00,
        elec_price_home=0.20,
        elec_price_work=0.20,
        elec_price_public=0.50,
        w_home=0.90,
        w_work=0.00,
        w_public=0.10,
        maint_6y_chf=3_000.0,
        tires_base_chf=1_000.0,
        phev_share_elec=0.5 if tech == Tech.PHEV else 0.0,
    )


def two_sliders_sum_to_one(label_a: str, label_b: str, default_a: float, default_b: float, key_prefix: str = ""):
    """Retourne (a, b, c) avec a+b+c=1 (via 2 sliders pour a et b ; c = 1 - a - b)."""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        a = st.slider(f"{label_a} (%)", 0, 100, int(default_a * 100), key=f"{key_prefix}_a") / 100.0
    with col2:
        b = st.slider(f"{label_b} (%)", 0, 100, int(default_b * 100), key=f"{key_prefix}_b") / 100.0
    c = max(0.0, min(1.0, 1.0 - a - b))
    with col3:
        st.metric("Déplacement (%)", f"{int(round(c*100))}")
    return a, b, c


def check_decomposition(res, params, tol=0.01):
    """
    Vérifie que |NPV| ~= CAPEX_net + OPEX_actualisés (à tolérance près).
    Retourne (ok, abs_npv, capex_net, opex_disc).
    """
    r = float(params.discount_rate)
    df = res.annual_table.copy()

    # facteur d'actualisation par année (Année commence à 1)
    df["df"] = (1.0 + r) ** df["Année"]

    # OPEX actualisés (sommes par poste)
    e = float((df["Énergie"]     / df["df"]).sum())
    m = float((df["Maintenance"] / df["df"]).sum())
    t = float((df["Pneus"]       / df["df"]).sum())
    o = float((df["Autres"]      / df["df"]).sum()) if "Autres" in df.columns else 0.0
    opex_disc = e + m + t + o

    # CAPEX net = Achat - VR actualisée
    purchase = float(df.attrs.get("purchase_price", 0.0))
    years    = int(df["Année"].iloc[-1])
    vr_disc  = float(res.residual_value_nominal) / ((1.0 + r) ** years)
    capex_net = purchase - vr_disc

    abs_npv = abs(float(res.npv_total))
    ok = abs(abs_npv - (capex_net + opex_disc)) <= float(tol)
    return ok, abs_npv, capex_net, opex_disc


# ============================ UI ============================

st.set_page_config(page_title="TCO Ref — BFE/EBP 2023", page_icon="📊", layout="wide")
st.title("Calculateur TCO (référence méthodo BFE/EBP 2023) — MVP")

st.sidebar.markdown("### Paramètres globaux")
years = st.sidebar.slider("Horizon (années)", 3, 15, 8)
km_per_year = st.sidebar.number_input("Kilométrage annuel (km/an)", 0, 100_000, 15_000, step=1_000)

with st.sidebar.expander("⚙️ Plus de paramètres (globaux)"):
    discount_rate = st.number_input("Taux d’actualisation r (%)", 0.0, 15.0, 4.0, step=0.5) / 100.0
    energy_inflation = st.number_input("Inflation énergie (%/an)", -5.0, 50.0, 2.0, step=0.5) / 100.0
    opex_inflation = st.number_input("Inflation OPEX (%/an)", -5.0, 20.0, 1.5, step=0.5) / 100.0
    include_tires_x2 = st.checkbox("Pneus ×2 (méthodo)", True)
    apply_maint_7_over_6 = st.checkbox("Maintenance règle 7/6 → 8 ans (placeholder)", True)

global_params = GlobalParams(
    years=years,
    km_per_year=km_per_year,
    discount_rate=discount_rate,
    energy_inflation=energy_inflation,
    opex_inflation=opex_inflation,
    include_tires_x2=include_tires_x2,
    apply_maint_7_over_6=apply_maint_7_over_6,
)

st.divider()
st.subheader("Hypothèses (placeholders)")

st.markdown("### Paramètres énergie")
with st.expander("⚡ Prix énergie"):
    fuel_price = st.number_input("Prix carburant (CHF/L)", 0.0, 5.0, 2.00, step=0.01)
    colh, colw, colp = st.columns(3)
    with colh:
        elec_home = st.number_input("Élec. Maison (CHF/kWh)", 0.0, 1.0, 0.20, step=0.01)
    with colw:
        elec_work = st.number_input("Élec. Travail (CHF/kWh)", 0.0, 1.0, 0.20, step=0.01)
    with colp:
        elec_public = st.number_input("Élec. Déplacement (CHF/kWh)", 0.0, 2.0, 0.50, step=0.01)

with st.expander("🔌 Profil de recharge BEV/PHEV"):
    w_home, w_work, w_public = two_sliders_sum_to_one(
        "Maison", "Travail", default_a=0.90, default_b=0.00, key_prefix="recharge"
    )
    st.caption(f"Somme = 100% • Maison {int(w_home*100)}% • Travail {int(w_work*100)}% • Déplacement {int(w_public*100)}%")

# Specs par techno + injection UI
spec_ice = make_spec(Tech.ICE)
spec_bev = make_spec(Tech.BEV)
spec_phev = make_spec(Tech.PHEV)

for spec in (spec_ice, spec_bev, spec_phev):
    spec.fuel_price_chf_per_l = float(fuel_price)
    spec.elec_price_home = float(elec_home)
    spec.elec_price_work = float(elec_work)
    spec.elec_price_public = float(elec_public)
    spec.w_home = float(w_home)
    spec.w_work = float(w_work)
    spec.w_public = float(w_public)

# (temporaire) part élec PHEV
spec_phev.phev_share_elec = 0.5

specs_by_tech = {
    Tech.ICE: spec_ice,
    Tech.BEV: spec_bev,
    Tech.PHEV: spec_phev,
}

# ============================ Calcul ============================

results = compute_all_techs(global_params, specs_by_tech)

# ======================= Visualisations ========================

st.divider()
st.subheader("Visualisations & cohérence")

# A) Décomposition par poste (somme = |NPV|)
df_decomp = make_decomposition_df_by_post(results, global_params)
fig_bar = fig_bar_decomposition_by_post(df_decomp)
st.plotly_chart(fig_bar, use_container_width=True)

# B) Courbe du cumul des coûts actualisés (axe Y ≥ 0)
cum_df = make_cum_df(results)
fig_line = fig_line_cumulative(cum_df)
st.plotly_chart(fig_line, use_container_width=True)

# C) Contrôle de cohérence
for tech in [Tech.ICE, Tech.BEV, Tech.PHEV]:
    ok, abs_npv, capex_net, opex_disc = check_decomposition(results[tech], global_params, tol=0.01)
    msg = f"{tech.value}: |NPV|={abs_npv:,.0f} vs CAPEX_net={capex_net:,.0f} + OPEX={opex_disc:,.0f}"
    (st.success if ok else st.error)(("OK — " if ok else "Écart — ") + msg)

# D) Export agrégé
st.subheader("Export")

agg = df_decomp.pivot_table(index="Technologie", columns="Poste", values="CHF", aggfunc="sum").reset_index()

POSTS = ["Acquisition (achat – VR act.)", "Énergie", "Maintenance", "Pneus", "Autres"]
for p in POSTS:
    if p not in agg.columns:
        agg[p] = 0.0
agg["Total (somme postes)"] = agg[POSTS].sum(axis=1)

st.dataframe(agg, use_container_width=True)

def _to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.download_button("⬇️ Décomp. (CSV)", data=_to_csv(df_decomp), file_name="decomposition.csv", mime="text/csv")
with col_b:
    st.download_button("⬇️ Agrégé (CSV)", data=_to_csv(agg), file_name="aggregat.csv", mime="text/csv")
with col_c:
    st.download_button("⬇️ BEV annuel (CSV)", data=_to_csv(results[Tech.BEV].annual_table), file_name="bev_annuel.csv", mime="text/csv")
with col_d:
    st.download_button("⬇️ ICE annuel (CSV)", data=_to_csv(results[Tech.ICE].annual_table), file_name="ice_annuel.csv", mime="text/csv")

# ======================== Récapitulatif ========================

st.markdown("## Résultats (NPV et TCO/km)")
recap = []
for tech in [Tech.ICE, Tech.BEV, Tech.PHEV]:
    r = results[tech]
    recap.append({
        "Technologie": tech.value,
        "Classe": r.vehicle_class,
        "NPV total (CHF)": f"{r.npv_total:,.0f}",
        "TCO (CHF/km)": f"{r.tco_per_km:.2f}",
    })
st.dataframe(pd.DataFrame(recap), use_container_width=True)

with st.expander("Voir la table annuelle détaillée (BEV)"):
    st.dataframe(results[Tech.BEV].annual_table, use_container_width=True)
