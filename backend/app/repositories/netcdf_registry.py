from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatasetDescriptor:
    dataset_id: str
    path: Path
    variable: str
    source_variable: str
    provider: str
    spatial_coverage: dict[str, float]
    timestamps: tuple[str, ...]
    depths: tuple[float, ...]

    def supports(self, *, timestamp: str | None = None, depth: float | None = None) -> bool:
        if timestamp is not None and timestamp not in self.timestamps:
            return False
        if depth is not None and not self.depths:
            return False
        return depth is None or min(self.depths) <= depth <= max(self.depths)


class NetCDFDatasetRegistry:
    """Discovers and validates local NetCDF datasets at application startup."""

    SUPPORTED_VARIABLES = {'thetao': 'temperature', 'so': 'salinity', 'uo': 'current_u', 'vo': 'current_v'}
    COORDINATES = {
        'time': ('time', 'valid_time'),
        'depth': ('depth', 'deptht', 'lev'),
        'latitude': ('latitude', 'lat'),
        'longitude': ('longitude', 'lon'),
    }

    def __init__(self, data_dir: str | Path, *, pattern: str = '*.nc') -> None:
        self.data_dir = Path(data_dir)
        self.pattern = pattern
        self.datasets: list[DatasetDescriptor] = []

    def discover(self) -> list[DatasetDescriptor]:
        self.datasets = []
        if not self.data_dir.exists():
            logger.warning('NetCDF data directory does not exist: %s', self.data_dir)
            return []
        for path in sorted(self.data_dir.glob(self.pattern)):
            try:
                descriptors = self._validate(path)
            except (OSError, RuntimeError, ValueError) as exc:
                logger.warning('Skipping invalid NetCDF dataset %s: %s', path.name, exc)
                continue
            self.datasets.extend(descriptors)
            for descriptor in descriptors:
                logger.info('Discovered NetCDF dataset %s (%s)', path.name, descriptor.variable)
        return list(self.datasets)

    def by_variable(self, variable: str) -> list[DatasetDescriptor]:
        return [dataset for dataset in self.datasets if dataset.variable == variable]

    def _validate(self, path: Path) -> list[DatasetDescriptor]:
        if not path.is_file():
            raise ValueError('not a regular file')
        try:
            import xarray as xr
            dataset = xr.open_dataset(path)
        except ImportError as exc:
            raise RuntimeError('xarray is required for NetCDF discovery') from exc
        try:
            source_variables = [name for name in self.SUPPORTED_VARIABLES if name in dataset.data_vars]
            if not source_variables:
                raise ValueError('no supported ocean variable')
            coordinate_names = {
                key: next((name for name in names if name in dataset.coords or name in dataset.dims), None)
                for key, names in self.COORDINATES.items()
            }
            missing = [key for key, name in coordinate_names.items() if name is None]
            if missing:
                raise ValueError(f'missing coordinates: {", ".join(missing)}')
            required_dimensions = {coordinate_names[key] for key in self.COORDINATES}
            invalid_variables = [name for name in source_variables if not required_dimensions.issubset(dataset[name].dims)]
            if invalid_variables:
                raise ValueError(f'ocean variable dimensions do not match coordinates: {", ".join(invalid_variables)}')
            coverage = {
                'min_latitude': float(dataset[coordinate_names['latitude']].values.min()),
                'max_latitude': float(dataset[coordinate_names['latitude']].values.max()),
                'min_longitude': float(dataset[coordinate_names['longitude']].values.min()),
                'max_longitude': float(dataset[coordinate_names['longitude']].values.max()),
            }
            timestamps = tuple(self._serialize_time(value) for value in dataset[coordinate_names['time']].values)
            depths = tuple(float(value) for value in dataset[coordinate_names['depth']].values)
            return [
                DatasetDescriptor(
                    dataset_id=path.stem,
                    path=path,
                    variable=self.SUPPORTED_VARIABLES[source_variable],
                    source_variable=source_variable,
                    provider='Copernicus Marine',
                    spatial_coverage=coverage,
                    timestamps=timestamps,
                    depths=depths,
                )
                for source_variable in source_variables
            ]
        finally:
            dataset.close()

    @staticmethod
    def _serialize_time(value: Any) -> str:
        from app.repositories.copernicus_netcdf_repository import CopernicusNetCDFRepository

        return CopernicusNetCDFRepository._serialize_timestamp(value)