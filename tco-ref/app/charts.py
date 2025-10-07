#nouvelle version
from __future__ import annotations
from typing import Dict
import pandas as pd
import altair as alt

from tco_core.models import Tech, Results, GlobalParams

TECH_LABELS = {
    'BEV': 'VE',
    'ICE': 'VT',
    'PHEV': 'VHR',
}
TECH_ORDER_LABELS = ['VE', 'VT', 'VHR']

# Fonction utilitaire pour générer le DataFrame des dépenses par catégorie (manquante)
def make_expenses_by_category_df(results: Dict[Tech, Results]) -> pd.DataFrame:
    """
    Build a long-format DataFrame with expense categories over time.
    Returns DataFrame with columns: ["Année", "Technologie", "Poste", "CHF"]
    where each row represents: year, technology, expense category, amount
    """
    rows = []
    expense_columns = ["Énergie", "Maintenance", "Pneus", "Autres"]
    for tech, res in results.items():
        df = res.annual_table.copy()
        for _, row in df.iterrows():
            year = int(row["Année"])
            for poste in expense_columns:
                amount = float(row.get(poste, 0.0))
                rows.append({
                    "Année": year,
                    "Technologie": TECH_LABELS.get(tech.value, tech.value),
                    "Poste": poste,
                    "CHF": amount
                })
    return pd.DataFrame(rows)


def format_chf_swiss(value: float) -> str:
    """Format number with Swiss thousand separator (apostrophe)."""
    return f"{round(value):_}".replace("_", "'")


def make_decomposition_df_by_post(results: Dict[Tech, Results], params: GlobalParams) -> pd.DataFrame:
    """
    Table longue avec 5 postes par techno :
      - Acquisition (CAPEX net = Achat – VR actualisée)
      - Énergie (somme des coûts d'énergie actualisés)
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
        vr_disc  = float(res.residual_value_discounted)
        capex_net = purchase - vr_disc

        label = TECH_LABELS.get(tech.value, tech.value)
        rows += [
            {"Technologie": label, "Poste": "Acquisition (achat – VR act.)", "CHF": capex_net},
            {"Technologie": label, "Poste": "Énergie",                        "CHF": e_disc},
            {"Technologie": label, "Poste": "Maintenance",                    "CHF": m_disc},
            {"Technologie": label, "Poste": "Pneus",                          "CHF": t_disc},
            {"Technologie": label, "Poste": "Autres",                         "CHF": o_disc},
        ]

    return pd.DataFrame(rows)


def fig_bar_decomposition_by_post(df_decomp: pd.DataFrame):
    """
    Create a stacked bar chart with Altair showing TCO decomposition.
    Features: rounded corners, vibrant colors, total labels on top.
    """

    df_decomp = df_decomp.copy()
    df_decomp["CHF_formatted"] = df_decomp["CHF"].apply(lambda x: format_chf_swiss(x))

    # Forcer explicitement le type catégoriel pour garantir l'ordre
    df_decomp["Technologie"] = pd.Categorical(df_decomp["Technologie"], categories=TECH_ORDER_LABELS, ordered=True)

    # S'assurer que toutes les catégories sont présentes (même vides)
    for tech in TECH_ORDER_LABELS:
        if tech not in df_decomp["Technologie"].values:
            for poste in ["Acquisition (achat – VR act.)", "Énergie", "Maintenance", "Pneus", "Autres"]:
                df_decomp = pd.concat([
                    df_decomp,
                    pd.DataFrame([{"Technologie": tech, "Poste": poste, "CHF": 0.0, "CHF_formatted": "0"}])
                ], ignore_index=True)
    df_decomp["Technologie"] = pd.Categorical(df_decomp["Technologie"], categories=TECH_ORDER_LABELS, ordered=True)

    color_scale = alt.Scale(
        domain=[
            "Autres",
            "Pneus",
            "Maintenance",
            "Énergie",
            "Acquisition (achat – VR act.)"
        ],
        range=["#fd7979", "#ffa77f", "#ffcc8f", "#b3cbff", "#4371c4"]
    )

    totals = df_decomp.groupby("Technologie", as_index=False)["CHF"].sum()
    totals["CHF_formatted"] = totals["CHF"].apply(lambda x: f"{format_chf_swiss(x)} CHF")
    totals["Technologie"] = pd.Categorical(totals["Technologie"], categories=TECH_ORDER_LABELS, ordered=True)

    bars = alt.Chart(df_decomp).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
        x=alt.X("Technologie:N", axis=alt.Axis(title=None, labelAngle=0), sort=TECH_ORDER_LABELS),
        y=alt.Y(
            "CHF:Q", 
            axis=alt.Axis(
                title="CHF",
                labelExpr='replace(format(datum.value, ",.0f"), ",", "\u0027")'
            ), 
            scale=alt.Scale(domain=[0, totals["CHF"].max() * 1.15])
        ),
        color=alt.Color("Poste:N", scale=color_scale, legend=alt.Legend(orient="top", title=None, labelLimit=300)),
        tooltip=[
            alt.Tooltip("Technologie:N", title="Technologie"),
            alt.Tooltip("Poste:N", title="Poste"),
            alt.Tooltip("CHF_formatted:N", title="Montant")
        ]
    ).properties(
        width='container',
        height=480,
        title={
            "text": "Coûts totaux",
            "fontSize": 20,
            "anchor": "start"
        }
    )

    text = alt.Chart(totals).mark_text(
        dy=-10,
        fontSize=14,
        fontWeight="bold"
    ).encode(
        x=alt.X("Technologie:N", sort=TECH_ORDER_LABELS),
        y=alt.Y("CHF:Q"),
        text="CHF_formatted:N"
    )

    chart = (bars + text).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    )

    return chart


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
    """
    Create a line chart with Altair showing cumulative costs over time.
    """
    if cum_df.empty:
        return alt.Chart(pd.DataFrame({"x": [0], "y": [0]})).mark_text(
            text="Aucune donnée disponible",
            size=16
        ).properties(width=600, height=400)
    
    if cum_df.empty:
        line = alt.Chart(pd.DataFrame({"x": [0], "y": [0]})).mark_text(
            text="Aucune donnée disponible",
            size=16
        ).properties(width=600, height=400)
    else:
        cum_df_clean = cum_df.copy()
        cum_df_clean = cum_df_clean.dropna()
        if cum_df_clean.empty:
            line = alt.Chart(pd.DataFrame({"x": [0], "y": [0]})).mark_text(
                text="Aucune donnée disponible",
                size=16
            ).properties(width=600, height=400)
        else:
            cum_df_clean["Technologie"] = cum_df_clean["Technologie"].map(TECH_LABELS).astype(pd.CategoricalDtype(categories=TECH_ORDER_LABELS, ordered=True))
            cum_df_clean["Cumul_formatted"] = cum_df_clean["Cumul NPV positif"].apply(lambda x: format_chf_swiss(x))
            color_scale = alt.Scale(
                domain=TECH_ORDER_LABELS,
                range=["#4371c4", "#686868", "#ffc88a"]
            )
            y_max = cum_df_clean["Cumul NPV positif"].max() * 1.1
            line = alt.Chart(cum_df_clean).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("Année:Q", axis=alt.Axis(title="Année", format="d", grid=False), scale=alt.Scale(nice=True)),
                y=alt.Y(
                    "Cumul NPV positif:Q", 
                    axis=alt.Axis(
                        title="CHF",
                        labelExpr='replace(format(datum.value, ",.0f"), ",", "\u0027")',
                        grid=False
                    ), 
                    scale=alt.Scale(domain=[0, y_max])
                ),
                color=alt.Color("Technologie:N", scale=color_scale, legend=alt.Legend(orient="bottom", title=None, values=TECH_ORDER_LABELS)),
                tooltip=[
                    alt.Tooltip("Année:Q", title="Année", format="d"),
                    alt.Tooltip("Technologie:N", title="Technologie"),
                    alt.Tooltip("Cumul_formatted:N", title="Cumul")
                ]
            ).properties(
                width=600,
                height=400,
                title={
                    "text": "Evolution des coûts sur la durée de possession",
                    "fontSize": 20,
                    "anchor": "start"
                }
            )
    chart = line.configure_view(
        strokeWidth=0
    )
    return chart


def fig_line_expenses_by_category(df: pd.DataFrame, selected_categories: list[str], cumulative: bool = False):
    """
    Create a line chart showing evolution of expense categories over time using Altair.
    
    Args:
        df: DataFrame from make_expenses_by_category_df
        selected_categories: List of expense categories to display
        cumulative: If True, show cumulative values; if False, show annual values
    
    Returns:
        Altair Chart object
    """
    df_filtered = df[df["Poste"].isin(selected_categories)].copy()
    
    if df_filtered.empty:
        return alt.Chart(pd.DataFrame({"x": [0], "y": [0]})).mark_text(
            text="Aucune donnée à afficher",
            size=16
        ).properties(width=600, height=400)
    
    df_filtered["Tech_Poste"] = df_filtered["Technologie"] + " - " + df_filtered["Poste"]
    
    if cumulative:
        df_filtered = df_filtered.sort_values(by=["Tech_Poste", "Année"])
        df_filtered["CHF_display"] = df_filtered.groupby("Tech_Poste")["CHF"].cumsum()
        y_col = "CHF_display"
        title = "Évolution cumulée des coûts par poste"
        y_label = "CHF (cumulé)"
    else:
        df_filtered["CHF_display"] = df_filtered["CHF"]
        y_col = "CHF_display"
        title = "Évolution des coûts par poste"
        y_label = "CHF (annuel)"
    
    df_filtered = df_filtered.dropna()
    
    if df_filtered.empty:
        return alt.Chart(pd.DataFrame({"x": [0], "y": [0]})).mark_text(
            text="Aucune donnée à afficher",
            size=16
        ).properties(width=600, height=400)
    
    df_filtered["Montant_formatted"] = df_filtered[y_col].apply(lambda x: format_chf_swiss(x))
    
    y_max = df_filtered[y_col].max() * 1.1 if df_filtered[y_col].max() > 0 else 1000
    
    chart = alt.Chart(df_filtered).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("Année:Q", axis=alt.Axis(title="Année", format="d", grid=False), scale=alt.Scale(nice=True)),
        y=alt.Y(
            f"{y_col}:Q", 
            axis=alt.Axis(
                title=y_label,
                labelExpr="replace(format(datum.value, ',.0f'), ',', \"'\")",
                grid=False
            ), 
            scale=alt.Scale(domain=[0, y_max])
        ),
        color=alt.Color("Tech_Poste:N", legend=alt.Legend(orient="bottom", title=None, labelLimit=300)),
        tooltip=[
            alt.Tooltip("Année:Q", title="Année", format="d"),
            alt.Tooltip("Tech_Poste:N", title="Tech - Poste"),
            alt.Tooltip("Montant_formatted:N", title="Montant")
        ]
    ).properties(
        width=600,
        height=400,
        title={
            "text": title,
            "fontSize": 15,
            "anchor": "start"
        }
    )
    
    chart = chart.configure_view(
        strokeWidth=0
    )
    
    return chart
