from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

from .models import Tech


_DEFAULTS_CACHE: Dict[str, Dict[str, Dict[str, Any]]] | None = None


def load_defaults() -> Dict[str, Dict[str, Dict[str, Any]]]:
    global _DEFAULTS_CACHE
    
    if _DEFAULTS_CACHE is not None:
        return _DEFAULTS_CACHE
    
    defaults_path = Path(__file__).parent.parent / "data" / "processed" / "defaults_by_class.json"
    
    if not defaults_path.exists():
        raise FileNotFoundError(f"Defaults file not found at {defaults_path}")
    
    with open(defaults_path, "r", encoding="utf-8") as f:
        _DEFAULTS_CACHE = json.load(f)
    
    return _DEFAULTS_CACHE


def get_default(tech: Tech, vehicle_class: str) -> Dict[str, Any]:
    defaults = load_defaults()
    
    if vehicle_class not in defaults:
        valid_classes = ", ".join(defaults.keys())
        raise ValueError(f"Invalid vehicle class '{vehicle_class}'. Valid classes: {valid_classes}")
    
    tech_key = tech.value
    if tech_key not in defaults[vehicle_class]:
        valid_techs = ", ".join(defaults[vehicle_class].keys())
        raise ValueError(f"Invalid tech '{tech_key}' for class '{vehicle_class}'. Valid techs: {valid_techs}")
    
    return defaults[vehicle_class][tech_key]
