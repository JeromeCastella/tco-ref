# Plan d’action — Projet **tco-ref** (Calculateur TCO BFE/EBP 2023)

Ce document sert de guide d’onboarding et de feuille de route pour les contributrices/teurs au projet.

---

## 0) Contexte rapide

**Objectif** : calculer et comparer le TCO (NPV) de trois technologies (ICE/BEV/PHEV) selon la méthodologie **BFE/EBP 2023**, avec décomposition par postes (Acquisition net VR, Énergie, Maintenance, Pneus, Autres) et dataviz **Streamlit**.

**Structure du repo** (rappel) :
- `tco_core/` : cœur métier (modèles, séries de prix, cashflows, VR, validations…)
- `app/` : UI Streamlit (saisie, charts, exports)
- `data/` : doc source + defaults extraits
- `tests/` : pytest

---

## 1) Setup local (dev)

```bash
git clone https://github.com/JeromeCastella/tco-ref.git
cd tco-ref

# venv (Windows PowerShell)
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# Dépendances
pip install -r requirements.txt

# Tests unitaires
pytest -q

# Lancer l’app
streamlit run app/app.py
```
> Nota: `app/app.py` contient un petit “hack sys.path” local pour l’instant. On passera au packaging editable install (voir Phase 5).

---

## 2) Standards & conventions

- **Python ≥ 3.10**, typage via annotations.
- Style: black/isort (si présents), sinon PEP8 minimal.
- **Tests d’abord** sur la logique cœur (`tco_core`). L’UI est secondaire côté tests.
- **Tolérance NPV**: contrôles de cohérence à ±0.01 CHF.

---

## 3) Tâches à court terme (Phase 1 – cœur métier)

### 3.1 Defaults par classe (mini/compact/midsize/SUV)

**But** : pré-remplir l’UI avec des valeurs sourcées, standardiser l’accès aux defaults.

**Livrables**
- `data/processed/defaults_by_class.json`
- `tco_core/defaults.py` (loader + accès par `(tech, classe)`)

**Exemple JSON**
```json
{
  "midsize": {
    "ICE": {
      "purchase_price": 42000,
      "residual_rate_8y_hint": 0.28,
      "consumption_fuel_l_per_100": 6.8,
      "maint_6y_chf": 3200,
      "tires_base_chf": 1000
    },
    "BEV": {
      "purchase_price": 55000,
      "residual_rate_8y_hint": 0.35,
      "consumption_elec_kwh_per_100": 17.0,
      "maint_6y_chf": 2800,
      "tires_base_chf": 1000
    },
    "PHEV": {
      "purchase_price": 52000,
      "residual_rate_8y_hint": 0.32,
      "consumption_fuel_l_per_100": 5.0,
      "consumption_elec_kwh_per_100": 16.0,
      "maint_6y_chf": 3000,
      "tires_base_chf": 1000
    }
  }
}
```

**Tests**
- `tests/test_defaults.py` : charge le JSON, `get_default(tech, classe)`, vérifie hydratation UI.

---

### 3.2 Valeur résiduelle (VR) — règle méthodo

**But** : calculer VR année *N* avec “Retail 6y −10% relatif ⇒ extrapolation 8y”.

**Livrables**
- `tco_core/residual.py`: `residual_at_end(spec, years, method="bfe_2023") -> (vr_nominale, vr_actualisee)`
- **Intégration** : dans `tco_core/tco.py` utiliser :
  - **VR nominale** ajoutée comme **flux** en année finale (*cashflow*),
  - **VR actualisée** utilisée pour la **décomposition CAPEX net** (achat − VR act.).

**Tests**
- `tests/test_residual.py` : cas nominaux + bornes.

---

### 3.3 Maintenance 7/6 → 8 ans (méthodo)

**But** : remplacer l’uplift simpliste par la vraie règle de la doc (profil annuel).

**Livrables**
- `tco_core/maintenance.py`: `maintenance_series(spec, params, years)` → **profil annuel** (inflation OPEX appliquée).
- Utilisation dans `tco_core/cashflows.py`.

**Tests**
- `tests/test_maintenance.py` : somme 6 ans vs 7/6 à 8 ans, inflation, bornes années.

---

### 3.4 Pneus (remplacements discrets)

**But** : passer d’une répartition linéaire à des **remplacements discrets** (ex: tous les X km), selon la classe.

**Livrables**
- `tco_core/tires.py`: `tires_series(spec, params, years)` calcul des occurrences (km/an × années) + inflation OPEX.

**Tests**
- `tests/test_tires.py` : nombre de remplacements attendu, inflation, ×2 méthodo.

---

### 3.5 PHEV — part électrique & profil de recharge

**But** : calculer l’énergie PHEV comme un **mix élec/thermique**, où la part élec utilise le **prix pondéré** (Maison/Travail/Public).

**Livrables**
- `tco_core/cashflows.py` : `annual_energy_cost_phev()` + `weighted_electricity_price()` dans `build_energy_price_series()`.

**Tests**
- `tests/test_cashflows.py` : cas PHEV 0%, 50%, 100% élec; inflation énergie; cohérence unités.

---

## 4) UI/UX (Phase 2)

- **Expander “+ paramètres”** (énergie, inflations, conso par techno, switches maintenance/pneus).
- **Profil de recharge** : 2 sliders + 3ᵉ auto (somme 100%) + caption.
- **Classe véhicule** : select → charge defaults → hydrate l’UI (modifiable).
- **PHEV** : slider part élec (0–100%) + tooltip (prix pondéré).

**Tests manuels** : cohérence champs, format CHF, responsive.

---

## 5) Dataviz & cohérence (Phase 3)

- **Bar chart par poste** (Plotly) :  
  Acquisition (achat − VR act.), Énergie act., Maintenance act., Pneus act., Autres act.  
  → Label total **= |NPV|**.
- **Courbe cumulée** : axe Y ≥ 0; markers; tooltips clairs.
- **Table annuelle** (BEV/ICE/PHEV) : colonnes standard, export CSV.

**Validation**
- `validation.py` + message UI si |NPV| ≠ somme postes (tolérance ±0.01 CHF).

---

## 6) Données & scénarios (Phase 4)

- `data/examples/scenarios.csv` : scénarios (horizon, km/an, prix énergie).
- (Option) runner scénarios pour comparaisons (tableau + export CSV).

---

## 7) Qualité & packaging (Phase 5)

- Étoffer tests unitaires (VR, maintenance, pneus, PHEV, validation).
- Retirer le **hack sys.path** → packaging local :
  - `pyproject.toml` (project + deps + black/isort/ruff/mypy)
  - `pip install -e .`
- **pre-commit** (black/isort/ruff) et **CI GitHub** (pytest).

---

## 8) Déploiement (Phase 6)

- Pinner les versions dans `requirements.txt`.
- Streamlit Community Cloud (entry: `app/app.py`).
- Badge “Open in Streamlit” dans README.

---

## 9) Contribution workflow

- Branche par feature (`feat/...`, `fix/...`).
- PRs petites, **tests verts**, revue.
- Merge → bump CHANGELOG minimal.

---

## 10) Points d’attention

- **Unités** : BEV en CHF/kWh; ICE en CHF/L; conso en kWh/100 ou L/100.
- **Actualisation** : année 0 = achat (non actualisé). Années t=1..N actualisées par `(1+r)^t`.
- **Décomposition** : VR de fin est **actualisée** dans **CAPEX net**; la **NPV** intègre la **VR nominale** comme flux en année N.
- **Tolérances** : toujours comparer **|NPV|** pour l’égalité “somme des postes”.

---

### Checklist “démarrer une feature”

- [ ] Créer branche `feat/<nom>`
- [ ] Écrire tests unitaires (ou les compléter)
- [ ] Implémenter dans `tco_core/*` (logique cœur)
- [ ] Brancher UI `app/*` si nécessaire
- [ ] `pytest -q` OK
- [ ] `streamlit run app/app.py` (test manuel)
- [ ] PR + revue + merge
