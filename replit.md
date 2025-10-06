# TCO Reference Calculator

## Overview
This is a Streamlit-based web application for calculating Total Cost of Ownership (TCO) for different vehicle technologies (ICE, BEV, PHEV). The application implements the BFE/EBP 2023 methodology for TCO calculation.

**Current State:** Fully functional TCO calculator with Phase 1 core business logic complete (Oct 2025)

## Recent Changes

### Phase 1: Core Business Logic (Completed October 2025)
All five tasks implementing BFE/EBP 2023 methodology:

**Task 3.1 - Vehicle Class Defaults System** ✅
- Implemented JSON-based defaults for 4 vehicle classes (mini/compact/midsize/SUV) × 3 technologies
- Created `tco_core/defaults.py` with `load_defaults_by_class()` function
- Data stored in `data/processed/defaults_by_class.json`
- 19 tests validating class-specific defaults

**Task 3.2 - Residual Value Methodology** ✅
- Implemented BFE/EBP 2023 residual value calculation
- Year 6 base value with -10% adjustment for years 7-8 extrapolation
- Created `tco_core/residual.py` module
- 13 tests covering edge cases and methodology compliance

**Task 3.3 - Maintenance 7/6 Rule** ✅
- Implemented annual maintenance profile (7 events in years 1,3,5,7 / 6 events in years 2,4,6,8)
- Proper cost distribution per vehicle class and technology
- Created `tco_core/maintenance.py` with detailed tests
- 11 tests validating the 7/6 rule pattern

**Task 3.4 - Discrete Tire Replacements** ✅
- Implemented realistic tire replacement every 40,000 km
- Costs occur only when cumulative km crosses 40k/80k/120k thresholds
- Enhanced `tco_core/tires.py` with discrete logic
- 17 tests covering various mileage scenarios

**Task 3.5 - PHEV Weighted Electricity Price** ✅
- PHEV electric portion uses weighted electricity price: w_home × price_home + w_work × price_work + w_public × price_public
- Enhanced UI with charging profile controls and PHEV electric share slider
- Added real-time weighted price display
- 13 PHEV-specific tests validating weighted calculations

**Task 3.6 - Autres Coûts (Other Costs)** ✅
- Implemented BFE/EBP 2023 section 3.6 methodology for "other costs"
- **Taxe cantonale** : Swiss average per segment (Source: ASA Tableau 16)
  - Mini: 194 CHF/an, Compact: 275 CHF/an, Midsize: 356 CHF/an, SUV: 363 CHF/an
- **Assurance** : Vollkasko insurance, standard profile Aargau 43 years (Source: Comparis)
  - Segment and technology-specific annual premiums, constant over 8 years
- **Soins du véhicule** : 150 CHF/an (Source: TCS) - cleaning and routine care
- **Infrastructure de recharge** : 3'040 CHF for BEV/PHEV only, year 1 (Source: Helion/CKW)
  - 11 kW charging station, residual value = 0 after 8 years
- Calculation: Other_t = Tax (with OPEX inflation) + Insurance (constant) + Care (with OPEX inflation) + Infrastructure (if t=1 and BEV/PHEV)
- Created `other_costs_series()` function in `tco_core/cashflows.py`
- 18 tests validating infrastructure, inflation, and totals
- Validation against PDF Tableaux 19-20: results within expected range
- **Total test suite: 98 passing tests**

### UI Enhancement: Expense Category Filter (October 2025)
**Interactive Line Chart Analysis** ✅
- Added expense category filter for detailed cost evolution analysis
- Multi-select widget to choose expense categories (Énergie, Maintenance, Pneus, Autres)
- Toggle between annual and cumulative view
- Tech-Poste combinations displayed as separate lines (e.g., "ICE - Énergie", "BEV - Maintenance")
- Safe handling of missing columns with default 0.0 values
- Enhanced visualization section in app/charts.py with `make_expenses_by_category_df()` and `fig_line_expenses_by_category()`

### UX Improvements (October 2025)
**User-Friendly Interface Redesign** ✅
- **Technical data organization:** Analysis tools, coherence checks, and exports now in collapsible "🔧 Données techniques et exports" expander
- **Improved charging profile UI:** 3 constrained sliders (Maison, Travail, Déplacement) that automatically maintain 100% total - no possibility of invalid inputs
- **Better parameter accessibility:** Advanced parameters ("⚙️ Plus de paramètres") moved from sidebar to main body for easier access
- **Modern bar chart design:** 
  - Pastel color palette (blue, pink, orange tones)
  - Clean presentation with labels only on column totals
  - Detailed hover info for expense breakdown
  - Enhanced visual appeal and readability

## Project Information
- **Name:** tco-ref
- **Version:** 0.0.1
- **Technology:** Python 3.11 + Streamlit
- **Type:** Web Application
- **Port:** 5000

## Project Structure
```
.
├── app/                    # Streamlit application
│   ├── app.py             # Main application UI
│   └── charts.py          # Visualization components
├── tco_core/              # Core TCO calculation logic
│   ├── models.py          # Data models (Tech, GlobalParams, VehicleSpec, etc.)
│   ├── tco.py             # TCO computation engine
│   ├── energy.py          # Energy cost calculations
│   ├── maintenance.py     # Maintenance cost calculations
│   ├── tires.py           # Tire cost calculations
│   ├── cashflows.py       # Cashflow management
│   └── validation.py      # Data validation
├── tests/                 # Test suite
├── data/raw/              # Reference data (BFE_EBP_2023.pdf.pdf)
├── pyproject.toml         # Project configuration & dependencies
└── requirements.txt       # Python dependencies
```

## Features
- TCO calculation for three vehicle technologies:
  - ICE (Internal Combustion Engine)
  - BEV (Battery Electric Vehicle)
  - PHEV (Plug-in Hybrid Electric Vehicle)
- **Vehicle class defaults** for 4 categories: Petites voiture, Classe supérieure, Classe moyenne, SUV
- **BFE/EBP 2023 methodology compliance:**
  - Residual value: Year 6 base with -10% adjustment for years 7-8
  - Maintenance: 7/6 rule (alternating annual service events)
  - Tires: Discrete replacement every 40,000 km
  - PHEV: Weighted electricity price (home/work/public charging profiles)
- Interactive parameter adjustment
- Cost decomposition visualization (CAPEX, Energy, Maintenance, Tires)
- Cumulative cost tracking over time
- CSV export functionality
- NPV and TCO/km calculations

## Dependencies
- streamlit >= 1.37
- pandas >= 2.2
- numpy >= 1.26
- plotly >= 5.22
- altair >= 5.4
- pytest >= 8 (for testing)

## Development Setup
The project is installed in editable mode using:
```bash
pip install -e .
```

This allows the `tco_core` module to be imported by the Streamlit app.

## Running the Application
The application runs automatically via the Streamlit App workflow:
```bash
streamlit run app/app.py --server.port=5000 --server.address=0.0.0.0
```

## Deployment
Configured for autoscale deployment (stateless web app).

## Configuration Files
- `.streamlit/config.toml` - Streamlit server configuration (CORS, host binding)
- `pyproject.toml` - Python project configuration
- `.gitignore` - Python-specific ignores

## Notes
- The application uses placeholder data for vehicle specifications
- Calculations follow the BFE/EBP 2023 methodology
- The app includes data validation and consistency checks
- Screenshots are cached to prevent updates from being visible to users
