from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetBundle:
    """Canonical identity and source description for one coherent dataset."""

    dataset_id: str
    provider: str
    product: str
    model: str
    forecast_cycle: str | None
    variables: tuple[str, ...]
    coordinate_signature: tuple[tuple[str, str], ...]
    spatial_coverage: dict[str, float]
    temporal_coverage: dict[str, str]
    depth_levels: tuple[float, ...]
    source_files: dict[str, tuple[Path, ...]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def available_variables(self) -> tuple[str, ...]:
        return self.variables

    @property
    def available_depths(self) -> tuple[float, ...]:
        return self.depth_levels

    @property
    def path(self) -> Path:
        return next(iter(self.source_files.values()))[0]

    @property
    def variable(self) -> str:
        return next(iter(self.variables))

    @property
    def source_variable(self) -> str:
        return self.metadata.get('source_variables', {}).get(self.variable, self.variable)

    @property
    def timestamps(self) -> tuple[str, ...]:
        return tuple(self.metadata.get('timestamps', ()))

    def supports(self, *, timestamp: str | None = None, depth: float | None = None) -> bool:
        if timestamp is not None and timestamp not in self.timestamps:
            return False
        return depth is None or not self.depth_levels or min(self.depth_levels) <= depth <= max(self.depth_levels)