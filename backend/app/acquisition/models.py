from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScientificAcquisitionRequest:
    """Provider-neutral description of the scientific subset to acquire."""

    provider: str
    variables: tuple[str, ...]
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    product: str = 'physical-forecast'
    start_time: str | None = None
    end_time: str | None = None
    min_depth: float | None = None
    max_depth: float | None = None
    resolution: str | None = None
    forecast_cycle: str | None = None
