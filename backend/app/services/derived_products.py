"""Scientific products derived from normalized ocean variables."""

from __future__ import annotations

import math
from typing import Any


DERIVED_PRODUCTS = {
    'current_speed': {
        'name': 'Current speed',
        'units': 'm/s',
        'source_variables': ('current_u', 'current_v'),
    },
    'current_direction': {
        'name': 'Current direction',
        'units': 'degrees',
        'source_variables': ('current_u', 'current_v'),
    },
}


def calculate_current_speed(current_u: float | None, current_v: float | None) -> float | None:
    if current_u is None or current_v is None:
        return None
    return math.hypot(float(current_u), float(current_v))


def calculate_current_direction(current_u: float | None, current_v: float | None) -> float | None:
    if current_u is None or current_v is None:
        return None
    return math.degrees(math.atan2(float(current_v), float(current_u))) % 360.0


def calculate_derived_product(product: str, record: dict[str, Any]) -> float | None:
    calculators = {
        'current_speed': calculate_current_speed,
        'current_direction': calculate_current_direction,
    }
    try:
        calculator = calculators[product]
    except KeyError as exc:
        raise ValueError(f'Unsupported derived product: {product}') from exc
    return calculator(record.get('current_u'), record.get('current_v'))
