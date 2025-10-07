from __future__ import annotations
import json
import pytest
from pathlib import Path

from tco_core.defaults import load_defaults, get_default
from tco_core.models import Tech


class TestDefaults:
    
    def test_json_loads_correctly(self):
        defaults = load_defaults()
        assert isinstance(defaults, dict)
        assert len(defaults) > 0
    
    def test_all_vehicle_classes_present(self):
        defaults = load_defaults()
        expected_classes = ["petite", "superieure", "moyenne", "suv"]
        
        for vehicle_class in expected_classes:
            assert vehicle_class in defaults, f"Missing vehicle class: {vehicle_class}"
    
    def test_all_tech_types_present_in_each_class(self):
        defaults = load_defaults()
        expected_techs = ["ICE", "BEV", "PHEV"]
        
        for vehicle_class in defaults:
            for tech in expected_techs:
                assert tech in defaults[vehicle_class], \
                    f"Missing tech {tech} in class {vehicle_class}"
    
    def test_required_fields_present(self):
        defaults = load_defaults()
        required_fields = [
            "purchase_price",
            "residual_rate_8y_hint",
            "consumption_fuel_l_per_100",
            "consumption_elec_kwh_per_100",
            "maint_6y_chf",
            "tires_base_chf"
        ]
        
        for vehicle_class in defaults:
            for tech in defaults[vehicle_class]:
                for field in required_fields:
                    assert field in defaults[vehicle_class][tech], \
                        f"Missing field {field} in {vehicle_class}/{tech}"
    
    def test_get_default_retrieves_correct_values(self):
        result = get_default(Tech.ICE, "moyenne")
        
        assert isinstance(result, dict)
        assert "purchase_price" in result
        assert "residual_rate_8y_hint" in result
        assert result["purchase_price"] > 0
        assert 0 <= result["residual_rate_8y_hint"] <= 1
    
    def test_get_default_all_combinations(self):
        vehicle_classes = ["petite", "superieure", "moyenne", "suv"]
        techs = [Tech.ICE, Tech.BEV, Tech.PHEV]
        
        for vehicle_class in vehicle_classes:
            for tech in techs:
                result = get_default(tech, vehicle_class)
                assert isinstance(result, dict)
                assert len(result) > 0
    
    def test_get_default_invalid_class_raises_error(self):
        with pytest.raises(ValueError, match="Invalid vehicle class"):
            get_default(Tech.ICE, "invalid_class")
    
    def test_get_default_invalid_tech_raises_error(self):
        defaults = load_defaults()
        
        if "moyenne" in defaults:
            with pytest.raises(ValueError):
                tech_with_invalid_value = type('Tech', (), {'value': 'INVALID'})()
                get_default(tech_with_invalid_value, "moyenne")
    
    def test_bev_consumption_fuel_is_zero(self):
        vehicle_classes = ["petite", "superieure", "moyenne", "suv"]
        
        for vehicle_class in vehicle_classes:
            result = get_default(Tech.BEV, vehicle_class)
            assert result["consumption_fuel_l_per_100"] == 0.0, \
                f"BEV {vehicle_class} should have zero fuel consumption"
    
    def test_ice_consumption_elec_is_zero(self):
        vehicle_classes = ["petite", "superieure", "moyenne", "suv"]
        
        for vehicle_class in vehicle_classes:
            result = get_default(Tech.ICE, vehicle_class)
            assert result["consumption_elec_kwh_per_100"] == 0.0, \
                f"ICE {vehicle_class} should have zero electric consumption"
    
    def test_phev_has_both_consumptions(self):
        vehicle_classes = ["petite", "superieure", "moyenne", "suv"]
        
        for vehicle_class in vehicle_classes:
            result = get_default(Tech.PHEV, vehicle_class)
            assert result["consumption_fuel_l_per_100"] > 0, \
                f"PHEV {vehicle_class} should have fuel consumption"
            assert result["consumption_elec_kwh_per_100"] > 0, \
                f"PHEV {vehicle_class} should have electric consumption"
    
    def test_bev_residual_rate_higher_than_ice(self):
        vehicle_classes = ["petite", "superieure", "moyenne", "suv"]
        
        for vehicle_class in vehicle_classes:
            ice_result = get_default(Tech.ICE, vehicle_class)
            bev_result = get_default(Tech.BEV, vehicle_class)
            
            assert bev_result["residual_rate_8y_hint"] >= ice_result["residual_rate_8y_hint"], \
                f"BEV {vehicle_class} should have equal or higher residual rate than ICE"
    
    def test_bev_purchase_price_higher_than_ice(self):
        vehicle_classes = ["petite", "superieure", "moyenne", "suv"]
        
        for vehicle_class in vehicle_classes:
            ice_result = get_default(Tech.ICE, vehicle_class)
            bev_result = get_default(Tech.BEV, vehicle_class)
            
            assert bev_result["purchase_price"] > ice_result["purchase_price"], \
                f"BEV {vehicle_class} should be more expensive than ICE"
    
    def test_bev_maintenance_lower_than_ice(self):
        vehicle_classes = ["petite", "superieure", "moyenne", "suv"]
        
        for vehicle_class in vehicle_classes:
            ice_result = get_default(Tech.ICE, vehicle_class)
            bev_result = get_default(Tech.BEV, vehicle_class)
            
            assert bev_result["maint_6y_chf"] < ice_result["maint_6y_chf"], \
                f"BEV {vehicle_class} should have lower maintenance than ICE"
    
    def test_larger_vehicles_cost_more(self):
        class_order = ["petite", "superieure", "moyenne", "suv"]
        
        for tech in [Tech.ICE, Tech.BEV, Tech.PHEV]:
            prices = [get_default(tech, vc)["purchase_price"] for vc in class_order]
            
            for i in range(len(prices) - 1):
                assert prices[i] <= prices[i + 1], \
                    f"{tech.value}: {class_order[i]} should cost less than or equal to {class_order[i+1]}"
    
    def test_all_values_are_numeric(self):
        defaults = load_defaults()
        
        for vehicle_class in defaults:
            for tech in defaults[vehicle_class]:
                for field, value in defaults[vehicle_class][tech].items():
                    assert isinstance(value, (int, float)), \
                        f"{vehicle_class}/{tech}/{field} should be numeric, got {type(value)}"
    
    def test_all_values_are_non_negative(self):
        defaults = load_defaults()
        
        for vehicle_class in defaults:
            for tech in defaults[vehicle_class]:
                for field, value in defaults[vehicle_class][tech].items():
                    assert value >= 0, \
                        f"{vehicle_class}/{tech}/{field} should be non-negative, got {value}"
    
    def test_residual_rates_are_valid_fractions(self):
        defaults = load_defaults()
        
        for vehicle_class in defaults:
            for tech in defaults[vehicle_class]:
                residual = defaults[vehicle_class][tech]["residual_rate_8y_hint"]
                assert 0 <= residual <= 1, \
                    f"{vehicle_class}/{tech} residual rate should be between 0 and 1, got {residual}"
    
    def test_defaults_caching(self):
        first_call = load_defaults()
        second_call = load_defaults()
        
        assert first_call is second_call, "load_defaults should cache results"
