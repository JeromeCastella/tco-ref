from __future__ import annotations
from typing import List
import math
from .models import GlobalParams, VehicleSpec

TIRE_REPLACEMENT_INTERVAL_KM = 40000


def tires_series(spec: VehicleSpec, params: GlobalParams) -> List[float]:
    """
    Discrete tire replacement calculation based on km intervals.
    
    Logic:
      - Tires are replaced every TIRE_REPLACEMENT_INTERVAL_KM (e.g., 40,000 km)
      - Calculate which years replacements occur based on cumulative km
      - Apply tire cost (with include_tires_x2 multiplier) only in replacement years
      - Apply OPEX inflation for the specific year of replacement
      
    Args:
        spec: VehicleSpec with tires_base_chf
        params: GlobalParams with years, km_per_year, opex_inflation, include_tires_x2
        
    Returns:
        List of annual tire costs (CHF, nominal) for each year
    """
    years = int(params.years)
    km_per_year = float(params.km_per_year)
    
    if years <= 0 or km_per_year <= 0:
        return [0.0] * max(0, years)
    
    # Base tire cost with multiplier
    factor = 2.0 if params.include_tires_x2 else 1.0
    base_cost = float(spec.tires_base_chf) * factor
    
    # Initialize annual costs to zero
    annual_costs = [0.0] * years
    
    # Calculate replacements
    total_km = km_per_year * years
    num_replacements = int(math.ceil(total_km / TIRE_REPLACEMENT_INTERVAL_KM))
    
    for replacement_num in range(1, num_replacements + 1):
        # Calculate cumulative km at this replacement
        cumulative_km = replacement_num * TIRE_REPLACEMENT_INTERVAL_KM
        
        # Calculate which year this replacement occurs (1-indexed)
        # Use ceil to get the year when this km is reached
        year_of_replacement = int(math.ceil(cumulative_km / km_per_year))
        
        # Only add cost if replacement occurs within the analysis period
        if year_of_replacement <= years:
            # Apply inflation for this specific year (year 1 has no inflation)
            inflated_cost = base_cost * ((1.0 + params.opex_inflation) ** (year_of_replacement - 1))
            annual_costs[year_of_replacement - 1] += inflated_cost
    
    return annual_costs
