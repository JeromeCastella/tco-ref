from __future__ import annotations
from typing import Dict
import pandas as pd
import plotly.express as px

from tco_core.models import Tech, Results, GlobalParams


def make_decomposition_df_by_post(results: Dict[Tech, Results], params: GlobalParams) -> pd.DataFrame:
    """
    Table longue avec 5 postes par techno :
      - Acquisition (CAPEX net = Achat – VR actualisée)
      - Énergie (somme des coûts d’énergie actualisés)
      - Maintenance (actualisée)
      - Pneus (actualisée)
      - Autres (actualisée ; 0 si absent)
    La somme par techno == |NPV| (à la tolérance près).
    """
    rows = []
    r = float(params.discount_rate)

    for tech, res in results.items():
        df = res.annual_table.copy()
        df["df"] = (1.0 + r) ** df["Année"]

        e_disc = float((df["Énergie"]     / df["df"]).sum())
        m_disc = float((df["Maintenance"] / df["df"]).sum())
        t_disc = float((df["Pneus"]       / df["df"]).sum())
        o_disc = float((df["Autres"]      / df["df"]).sum()) if "Autres" in df.columns else 0.0

        purchase = float(df.attrs.get("purchase_price", 0.0))
        years    = int(df["Année"].iloc[-1])
        vr_nom   = float(res.residual_value_nominal)
        vr_disc  = vr_nom / ((1.0 + r) ** years)
        capex_net = purchase - vr_disc

        rows += [
            {"Technologie": tech.value, "Poste": "Acquisition (achat – VR act.)", "CHF": capex_net},
            {"Technologie": tech.value, "Poste": "Énergie",                        "CHF": e_disc},
            {"Technologie": tech.value, "Poste": "Maintenance",                    "CHF": m_disc},
            {"Technologie": tech.value, "Poste": "Pneus",                          "CHF": t_disc},
            {"Technologie": tech.value, "Poste": "Autres",                         "CHF": o_disc},
        ]

    return pd.DataFrame(rows)


def fig_bar_decomposition_by_post(df_decomp: pd.DataFrame):
    fig = px.bar(
        df_decomp,
        x="Technologie",
        y="CHF",
        color="Poste",
        barmode="stack",
        text_auto=".0f",
        title="Décomposition du TCO actualisé par poste",
    )
    fig.update_layout(
        plot_bgcolor="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False, title="CHF (actualisés)"),
        title=dict(x=0, xanchor="left", font=dict(size=20)),
        bargap=0.3,
        legend=dict(orientation="h", x=0, y=1.1),
    )
    totals = df_decomp.groupby("Technologie", as_index=False)["CHF"].sum()
    for _, row in totals.iterrows():
        fig.add_annotation(
            x=row["Technologie"],
            y=row["CHF"],
            text=f"{row['CHF']:,.0f} CHF",
            showarrow=False,
            font=dict(size=14, color="black"),
            yshift=10,
        )
    return fig


def make_cum_df(results: Dict[Tech, Results]) -> pd.DataFrame:
    """Assemble une table pour la courbe cumulée (coûts actualisés en positif)."""
    parts = []
    for tech, res in results.items():
        d = res.annual_table[["Année", "Cumul NPV"]].copy()
        d["Technologie"] = tech.value
        d["Cumul NPV positif"] = d["Cumul NPV"].abs()
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def fig_line_cumulative(cum_df: pd.DataFrame):
    fig = px.line(
        cum_df,
        x="Année",
        y="Cumul NPV positif",
        color="Technologie",
        title="Cumul des coûts actualisés",
        markers=True,
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        title=dict(x=0, xanchor="left", font=dict(size=15)),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="lightgrey", title="CHF (cumulé)", rangemode="tozero"),
        xaxis=dict(gridcolor="lightgrey"),
    )
    return fig
