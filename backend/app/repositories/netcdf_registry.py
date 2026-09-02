from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.models.dataset_bundle import DatasetBundle
logger = logging.getLogger(__name__)


DatasetDescriptor = DatasetBundle


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
        self.datasets: list[DatasetBundle] = []
        self.ready = False

    def discover(self) -> list[DatasetBundle]:
        self.datasets = []
        if not self.data_dir.exists():
            logger.warning('NetCDF data directory does not exist: %s', self.data_dir)
            self.ready = True
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
        self.ready = True
        return list(self.datasets)

    def by_variable(self, variable: str) -> list[DatasetBundle]:
        return [dataset for dataset in self.datasets if variable in dataset.available_variables]

    def _validate(self, path: Path) -> list[DatasetBundle]:
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
            temporal_coverage = {'start': timestamps[0], 'end': timestamps[-1]} if timestamps else {}
            source_files = {
                self.SUPPORTED_VARIABLES[source_variable]: (path,)
                for source_variable in source_variables
            }
            return [
                DatasetBundle(
                    dataset_id=path.stem,
                    provider='Copernicus Marine',
                    product=str(dataset.attrs.get('product', 'GLOBAL_ANALYSISFORECAST_PHY_001_024')),
                    model=str(dataset.attrs.get('model', 'Mercator Ocean GLO12')),
                    forecast_cycle=dataset.attrs.get('forecast_cycle'),
                    variables=tuple(self.SUPPORTED_VARIABLES[item] for item in source_variables),
                    coordinate_signature=tuple((key, coordinate_names[key]) for key in self.COORDINATES),
                    spatial_coverage=coverage,
                    temporal_coverage=temporal_coverage,
                    depth_levels=depths,
                    source_files=source_files,
                    metadata={'source_variables': {self.SUPPORTED_VARIABLES[item]: item for item in source_variables}, 'timestamps': timestamps},
                )
            ][:1]
        finally:
            dataset.close()

    @staticmethod
    def _serialize_time(value: Any) -> str:
        from app.repositories.copernicus_netcdf_repository import CopernicusNetCDFRepository

        return CopernicusNetCDFRepository._serialize_timestamp(value)