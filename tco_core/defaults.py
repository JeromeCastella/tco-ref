"""Utilities to load and access vehicle defaults grouped by class/technology."""
from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping

from .models import Tech

_PACKAGE_ROOT = Path(__file__).resolve().parent
_DEFAULTS_PATH = _PACKAGE_ROOT.parent / "data" / "processed" / "defaults_by_class.json"


@lru_cache(maxsize=None)
def _load_defaults_cached(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Defaults file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_defaults_by_class(path: str | Path | None = None) -> Dict[str, Any]:
    """Return the defaults grouped by vehicle class.

    Parameters
    ----------
    path:
        Optional path to the JSON file. When omitted, the project-level defaults
        file located under ``data/processed/defaults_by_class.json`` is used.

    Returns
    -------
    dict
        A *deep copy* of the defaults structure so callers can manipulate the
        returned mapping without mutating the cached data.
    """

    resolved_path = Path(path) if path is not None else _DEFAULTS_PATH
    data = _load_defaults_cached(str(resolved_path))
    return copy.deepcopy(data)


def _normalize_vehicle_class(defaults: Mapping[str, Any], vehicle_class: str) -> str:
    lookup = vehicle_class.lower()
    for key in defaults:
        if key.lower() == lookup:
            return key
    raise KeyError(f"Unknown vehicle class '{vehicle_class}' (available: {', '.join(defaults)})")


def _normalize_tech(tech: Tech | str) -> str:
    if isinstance(tech, Tech):
        return tech.value
    return str(tech).upper()


def get_defaults(
    tech: Tech | str,
    vehicle_class: str,
    defaults_by_class: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return defaults for a given (technology, vehicle class) pair.

    Parameters
    ----------
    tech:
        Either a :class:`tco_core.models.Tech` member or its string name.
    vehicle_class:
        The vehicle class identifier (case insensitive).
    defaults_by_class:
        Optional mapping already loaded via :func:`load_defaults_by_class`.

    Returns
    -------
    dict
        A dictionary copy with the defaults for the requested pair.
    """

    defaults = defaults_by_class or load_defaults_by_class()
    class_key = _normalize_vehicle_class(defaults, vehicle_class)
    tech_key = _normalize_tech(tech)

    try:
        tech_defaults = defaults[class_key][tech_key]
    except KeyError as exc:
        available = ", ".join(defaults[class_key])
        raise KeyError(
            f"Unknown tech '{tech}' for class '{class_key}' (available: {available})"
        ) from exc

    return copy.deepcopy(tech_defaults)


def residual_rate_from_defaults(defaults: Mapping[str, Any]) -> float:
    """Extract the residual rate from a defaults mapping."""

    residual = defaults.get("residual_rate_8y")
    if residual is None:
        residual = defaults.get("residual_rate_8y_hint")
    if residual is None:
        raise KeyError("Defaults mapping does not contain 'residual_rate_8y' or 'residual_rate_8y_hint'")
    return float(residual)


def apply_defaults(
    spec: MutableMapping[str, Any],
    defaults: Mapping[str, Any],
    *,
    include_consumption: bool = True,
) -> None:
    """Populate a mutable mapping with defaults values.

    Helper mainly used by the Streamlit app when building forms.
    """

    spec.update({
        "purchase_price": float(defaults["purchase_price"]),
        "residual_rate_8y": residual_rate_from_defaults(defaults),
        "maint_6y_chf": float(defaults["maint_6y_chf"]),
        "tires_base_chf": float(defaults["tires_base_chf"]),
    })
    if include_consumption:
        if "consumption_fuel_l_per_100" in defaults:
            spec["consumption_fuel_l_per_100"] = float(defaults["consumption_fuel_l_per_100"])
        if "consumption_elec_kwh_per_100" in defaults:
            spec["consumption_elec_kwh_per_100"] = float(defaults["consumption_elec_kwh_per_100"])
