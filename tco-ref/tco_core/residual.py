from __future__ import annotations
from typing import Tuple
import math

from .models import VehicleSpec, GlobalParams


def residual_at_end(
    spec: VehicleSpec,
    years: int,
    params: GlobalParams,
    method: str = "bfe_2023"
) -> Tuple[float, float]:
    """
    Calculate residual value (VR) according to specified methodology.
    
    Args:
        spec: Vehicle specification with purchase_price and residual_rate_8y_hint
        years: Number of years for the TCO calculation
        params: Global parameters including discount_rate
        method: Calculation method, default "bfe_2023"
    
    Returns:
        tuple: (vr_nominal, vr_discounted)
            - vr_nominal: Residual value at end of period (nominal CHF)
            - vr_discounted: Present value of residual (discounted CHF)
    
    BFE/EBP 2023 methodology:
        - residual_rate_8y_hint represents the residual rate at 6 years
        - VR_6 = purchase_price × residual_rate_8y_hint (no 0.9 adjustment)
        - VR_8 = VR_6 × 0.9 (10% reduction from year 6 to year 8)
        - For years < 6: linear interpolation from purchase_price to VR_6
        - For years > 6: geometric extrapolation with 0.9 factor over 2 years
    """
    if method != "bfe_2023":
        raise ValueError(f"Unsupported method: {method}. Only 'bfe_2023' is implemented.")
    
    purchase_price = float(spec.purchase_price)
    hint = float(spec.residual_rate_8y_hint)
    discount_rate = float(params.discount_rate)
    
    if years <= 0:
        return (purchase_price, purchase_price)
    
    # BFE/EBP 2023: Calculate VR at 6 years (NO 0.9 adjustment)
    vr_6 = purchase_price * hint
    
    # Calculate VR at target year
    if years < 6:
        # Linear interpolation from purchase_price (year 0) to VR_6 (year 6)
        # VR(t) = purchase_price - (purchase_price - VR_6) × (t/6)
        depreciation_to_6 = purchase_price - vr_6
        vr_nominal = purchase_price - (depreciation_to_6 * (years / 6.0))
    elif years == 6:
        vr_nominal = vr_6
    else:
        # years > 6: Geometric extrapolation
        # At year 8: VR_8 = VR_6 × 0.9 (10% reduction over 2 years)
        # Annual retention from year 6 to 8 = 0.9^(1/2)
        # For year t > 6: VR(t) = VR_6 × 0.9^((t-6)/2)
        
        if vr_6 > 0:
            # Calculate years beyond year 6
            years_beyond_6 = years - 6
            # Apply 0.9 factor over each 2-year period beyond year 6
            vr_nominal = vr_6 * (0.9 ** (years_beyond_6 / 2.0))
        else:
            # Edge case: if VR_6 is 0 or negative, vehicle has no value
            vr_nominal = 0.0
    
    # Ensure VR is non-negative and not greater than purchase price
    vr_nominal = max(0.0, min(purchase_price, vr_nominal))
    
    # Calculate discounted value
    if years > 0 and discount_rate >= 0:
        vr_discounted = vr_nominal / ((1.0 + discount_rate) ** years)
    else:
        vr_discounted = vr_nominal
    
    return (float(vr_nominal), float(vr_discounted))
