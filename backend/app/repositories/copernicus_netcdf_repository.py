from __future__ import annotations

import math
import logging
from itertools import product
from time import perf_counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from app.models.schemas import DatasetMetadata, ModelRecord
from app.repositories.base import BaseOceanRepository
from app.models.dataset_bundle import DatasetBundle
from app.repositories.exceptions import (
    DatasetUnavailableError,
    IncompatibleDatasetBundleError,
    InvalidProviderQueryError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class CopernicusNetCDFRepository(BaseOceanRepository):
    """Read locally staged Copernicus NetCDF files as normalized model data."""

    VARIABLE_FILES = {
        'temperature': ('temperature', 'thetao'),
        'salinity': ('salinity', 'so'),
        'current_u': ('current_u', 'uo'),
        'current_v': ('current_v', 'vo'),
    }
    COORDINATE_NAMES = {
        'time': ('time', 'valid_time'),
        'depth': ('depth', 'deptht', 'lev'),
        'latitude': ('latitude', 'lat'),
        'longitude': ('longitude', 'lon'),
    }

    def __init__(
        self,
        dataset: DatasetBundle | list[DatasetBundle] | Mapping[str, str | Path],
        *,
        dataset_id: str = 'copernicus-global-analysisforecast-phy-001-024',
        product: str = 'GLOBAL_ANALYSISFORECAST_PHY_001_024',
        model: str = 'Mercator Ocean GLO12',
    ) -> None:
        if isinstance(dataset, list):
            if not dataset:
                raise ValueError('At least one DatasetBundle is required.')
            self.dataset_bundles = tuple(dataset)
            first = dataset[0]
            source_files = {}
            for bundle in dataset:
                for field, paths in bundle.source_files.items():
                    source_files[field] = source_files.get(field, ()) + tuple(paths)
            self.dataset_bundle = DatasetBundle(
                dataset_id=first.dataset_id,
                provider=first.provider,
                product=first.product,
                model=first.model,
                forecast_cycle=first.forecast_cycle,
                variables=tuple(source_files),
                coordinate_signature=first.coordinate_signature,
                spatial_coverage=first.spatial_coverage,
                temporal_coverage=first.temporal_coverage,
                depth_levels=first.depth_levels,
                source_files=source_files,
                metadata={'bundles': dataset},
            )
        elif isinstance(dataset, DatasetBundle):
            self.dataset_bundles = (dataset,)
            self.dataset_bundle = dataset
        else:
            self.dataset_bundle = DatasetBundle(
                dataset_id=dataset_id,
                provider='Copernicus Marine',
                product=product,
                model=model,
                forecast_cycle=None,
                variables=tuple(dataset),
                coordinate_signature=(),
                spatial_coverage={},
                temporal_coverage={},
                depth_levels=(),
                source_files={
                    key: tuple(Path(item) for item in value) if isinstance(value, (list, tuple)) else (Path(value),)
                    for key, value in dataset.items()
                },
                metadata={},
            )
            self.dataset_bundles = (self.dataset_bundle,)
        self.dataset_paths = dict(self.dataset_bundle.source_files)
        self.dataset_id = self.dataset_bundle.dataset_id
        self.product = self.dataset_bundle.product
        self.model = self.dataset_bundle.model
        self._datasets: dict[str, Any] = {}
        self._coordinate_names: dict[str, dict[str, str]] = {}
        self._coordinate_names_by_dataset: dict[int, dict[str, str]] = {}
        self._validated_dataset_groups: set[tuple[tuple[str, str], ...]] = set()

    def _require_xarray(self) -> Any:
        try:
            import xarray as xr
        except ImportError as exc:
            raise RuntimeError('Copernicus NetCDF support requires xarray and a NetCDF backend.') from exc
        return xr

    def _dataset(self, field: str, path: Path | None = None) -> Any:
        if path is None:
            path = self.dataset_paths[field][0]
        cache_key = f'{field}:{path}'
        if cache_key in self._datasets:
            return self._datasets[cache_key]
        if field not in self.dataset_paths:
            raise DatasetUnavailableError(f'No local NetCDF file configured for {field}.')
        if not path.exists():
            raise DatasetUnavailableError(f'Missing local NetCDF file for {field}: {path}')
        try:
            dataset = self._require_xarray().open_dataset(path)
        except RuntimeError as exc:
            raise ProviderUnavailableError(str(exc)) from exc
        variable_name = self.VARIABLE_FILES[field][1]
        if variable_name not in dataset.data_vars:
            dataset.close()
            raise ValueError(f'NetCDF file for {field} does not contain variable {variable_name}.')
        self._coordinate_names[cache_key] = {
            name: self._coordinate_name(dataset, name)
            for name in self.COORDINATE_NAMES
        }
        self._coordinate_names_by_dataset[id(dataset)] = self._coordinate_names[cache_key]
        self._datasets[cache_key] = dataset
        return dataset

    def close(self) -> None:
        for dataset in self._datasets.values():
            dataset.close()
        self._datasets.clear()
        self._coordinate_names.clear()
        self._coordinate_names_by_dataset.clear()
        self._validated_dataset_groups.clear()

    def __enter__(self) -> 'CopernicusNetCDFRepository':
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_model_records(self) -> list[dict[str, Any]]:
        return self.get_ocean_records()

    def query_ocean_records(self, **filters: Any) -> list[dict[str, Any]]:
        self._validate_query(filters)
        return self.get_ocean_records(**filters)

    def query_ocean_point(self, *, latitude: float, longitude: float, depth: float, timestamp: str | datetime) -> dict[str, Any]:
        self._validate_query({'depth': depth, 'timestamp': timestamp, 'min_lat': latitude, 'max_lat': latitude, 'min_lon': longitude, 'max_lon': longitude})
        fields = self._fields_for(None)
        reference = self._dataset(fields[0])
        matched = self._nearest_record(reference, fields, latitude, longitude, depth, timestamp)
        return matched

    def get_observation_records(self) -> list[dict[str, Any]]:
        return []

    def get_provider_capabilities(self) -> dict[str, Any]:
        metadata = self.get_dataset_metadata()
        return {
            'provider': self.dataset_bundle.provider,
            'available_parameters': list(self.dataset_bundle.variables),
            'metadata': metadata,
            'depths': self._get_available_depths(),
            'timestamps': self._get_available_timestamps(),
        }

    def health(self) -> dict[str, Any]:
        try:
            metadata = self.get_dataset_metadata()
        except (DatasetUnavailableError, ProviderUnavailableError, ValueError) as exc:
            return {'available': False, 'provider': 'Copernicus Marine', 'error': str(exc)}
        return {'available': bool(metadata), 'provider': 'Copernicus Marine'}

    def get_bathymetry_records(self) -> list[dict[str, Any]]:
        return []

    def get_dataset_metadata(self) -> list[dict[str, Any]]:
        field = next(iter(self.dataset_paths), None)
        if field is None:
            return []
        dataset = self._dataset(field)
        coordinates = {
            name: dataset[self._coordinate_name(dataset, name)].values
            for name in self.COORDINATE_NAMES
            if self._coordinate_name(dataset, name, required=False)
        }
        coverage = {
            'min_latitude': float(coordinates['latitude'].min()),
            'max_latitude': float(coordinates['latitude'].max()),
            'min_longitude': float(coordinates['longitude'].min()),
            'max_longitude': float(coordinates['longitude'].max()),
        }
        timestamps = [self._serialize_timestamp(value) for value in coordinates.get('time', [])]
        metadata = DatasetMetadata(
            dataset_id=self.dataset_bundle.dataset_id,
            dataset_name=self.dataset_bundle.model,
            description='Copernicus Marine local NetCDF model data.',
            source=self.dataset_bundle.provider,
            source_type='model',
            spatial_coverage=coverage,
            time_range={'start': timestamps[0], 'end': timestamps[-1]} if timestamps else {},
            resolution='; '.join(f'{name}={len(values)}' for name, values in coordinates.items()),
            variables=[field for field in self.dataset_paths if field in self.VARIABLE_FILES],
            units={field: self._unit_for(self._dataset(field), field) for field in self.dataset_paths},
            last_updated=timestamps[-1] if timestamps else '',
            is_synthetic=False,
        )
        return [metadata.model_dump(mode='json')]

    def _get_available_depths(self) -> list[float]:
        dataset = self._dataset(next(iter(self.dataset_paths)))
        coordinate = self._coordinate_name(dataset, 'depth')
        return [float(value) for value in dataset[coordinate].values]

    def _get_available_timestamps(self) -> list[str]:
        dataset = self._dataset(next(iter(self.dataset_paths)))
        coordinate = self._coordinate_name(dataset, 'time')
        return [self._serialize_timestamp(value) for value in dataset[coordinate].values]

    def get_ocean_records(
        self,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        started = perf_counter()
        try:
            return self._get_ocean_records(**filters)
        finally:
            logger.info('NetCDF query completed in %.3f seconds', perf_counter() - started)

    def _get_ocean_records(
        self,
        *,
        parameter: str | None = None,
        depth: float | None = None,
        timestamp: str | datetime | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        if source is not None and source.lower() not in {'model', 'copernicus marine'}:
            raise InvalidProviderQueryError(f'Unsupported source: {source}')
        fields = self._fields_for(parameter)
        selected_paths = {field: self._select_path(field, depth, timestamp, min_lat, max_lat, min_lon, max_lon) for field in fields}
        if any(path is None for path in selected_paths.values()):
            return []
        selections = self._select_coordinates(
            self._dataset(fields[0], selected_paths[fields[0]]),
            depth=depth,
            timestamp=timestamp,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        self._validate_selected_datasets(selected_paths)
        coordinate_values = {
            name: selections[f'{name}_values'][selections[name]]
            for name in self.COORDINATE_NAMES
        }
        vectorized_values = {
            field: self._vectorized_values(
                self._dataset(field, selected_paths[field]),
                field,
                coordinate_values,
            )
            for field in fields
        }
        records = []
        grid_shape = tuple(len(coordinate_values[name]) for name in self.COORDINATE_NAMES)
        for flat_index, indexes in enumerate(product(*(range(size) for size in grid_shape))):
            values = {
                field: self._numeric_value(vectorized_values[field].reshape(-1)[flat_index])
                for field in fields
            }
            time_index, depth_index, latitude_index, longitude_index = indexes
            record = {
                'dataset_id': self.dataset_id,
                'source_type': 'model',
                'source': self.dataset_bundle.provider,
                'provider': self.dataset_bundle.provider,
                'product': self.dataset_bundle.product,
                'model': self.dataset_bundle.model,
                'is_synthetic': False,
                'latitude': float(coordinate_values['latitude'][latitude_index]),
                'longitude': float(coordinate_values['longitude'][longitude_index]),
                'depth': float(coordinate_values['depth'][depth_index]),
                'requested_depth': depth,
                'matched_depth': float(coordinate_values['depth'][depth_index]),
                'timestamp': self._serialize_timestamp(coordinate_values['time'][time_index]),
                'temperature': values.get('temperature'),
                'salinity': values.get('salinity'),
                'current_u': values.get('current_u'),
                'current_v': values.get('current_v'),
                'current_speed': self._current_speed(values.get('current_u'), values.get('current_v')),
            }
            normalized = ModelRecord.model_validate(record).model_dump(mode='json')
            records.append(normalized | {key: record[key] for key in ('requested_depth', 'matched_depth', 'provider', 'product', 'model', 'is_synthetic', 'current_speed')})
        return records

    def _select_path(self, field: str, depth: float | None, timestamp: str | datetime | None, min_lat: float | None, max_lat: float | None, min_lon: float | None, max_lon: float | None) -> Path | None:
        candidates = self.dataset_paths.get(field, [])
        for path in candidates:
            dataset = self._dataset(field, path)
            try:
                selections = self._select_coordinates(dataset, depth=depth, timestamp=timestamp, min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon)
                if any(not selections[name] for name in ('time', 'depth', 'latitude', 'longitude')):
                    continue
                return path
            except (IndexError, ValueError):
                continue
        if candidates:
            return None
        raise ValueError(f'No local NetCDF file configured for {field}.')

    def _fields_for(self, parameter: str | None) -> tuple[str, ...]:
        if parameter in (None, 'all'):
            return tuple(field for field in self.VARIABLE_FILES if field in self.dataset_paths)
        if parameter == 'current':
            return ('current_u', 'current_v')
        if parameter not in self.VARIABLE_FILES:
            raise InvalidProviderQueryError(f'Unsupported parameter: {parameter}')
        return (parameter,)

    def _validate_selected_datasets(self, selected_paths: dict[str, Path]) -> None:
        group_key = tuple((field, str(path)) for field, path in selected_paths.items())
        if group_key in self._validated_dataset_groups:
            return
        selected = [(field, self._dataset(field, path)) for field, path in selected_paths.items()]
        if not selected:
            return
        reference_field, reference_dataset = selected[0]
        reference = self._coordinate_definition(reference_dataset)
        reference_dimensions = tuple(reference_dataset[self.VARIABLE_FILES[reference_field][1]].dims)
        for field, dataset in selected[1:]:
            current = self._coordinate_definition(dataset)
            dimensions = tuple(dataset[self.VARIABLE_FILES[field][1]].dims)
            if current != reference or dimensions != reference_dimensions:
                raise IncompatibleDatasetBundleError(
                    'Selected NetCDF files have incompatible coordinate definitions.'
                )
        self._validated_dataset_groups.add(group_key)

    def _coordinate_definition(self, dataset: Any) -> tuple[Any, ...]:
        definition = []
        for name in self.COORDINATE_NAMES:
            coordinate_name = self._coordinate_name(dataset, name)
            coordinate = dataset[coordinate_name]
            values = coordinate.values
            comparable_values = tuple(sorted(self._coordinate_value(value, name) for value in values.flat))
            definition.append((name, coordinate_name, tuple(coordinate.dims), tuple(coordinate.shape), comparable_values))
        return tuple(definition)

    @staticmethod
    def _coordinate_value(value: Any, coordinate: str) -> Any:
        if coordinate == 'time':
            return CopernicusNetCDFRepository._normalize_datetime(value)
        return float(value)

    def _vectorized_values(self, dataset: Any, field: str, coordinate_values: dict[str, Any]) -> Any:
        coordinate_names = self._coordinate_names_by_dataset[id(dataset)]
        indexers = {
            coordinate_names[name]: values
            for name, values in coordinate_values.items()
            if coordinate_names[name] in dataset[self.VARIABLE_FILES[field][1]].dims
        }
        data = dataset[self.VARIABLE_FILES[field][1]].sel(indexers)
        dimensions = tuple(coordinate_names[name] for name in self.COORDINATE_NAMES)
        return data.transpose(*dimensions).values

    @staticmethod
    def _numeric_value(value: Any) -> float | None:
        try:
            numeric = float(value)
            return numeric if math.isfinite(numeric) else None
        except (TypeError, ValueError):
            return None

    def _validate_query(self, filters: dict[str, Any]) -> None:
        latitude = filters.get('latitude')
        longitude = filters.get('longitude')
        if latitude is not None and not -90 <= float(latitude) <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees.')
        if longitude is not None and not -180 <= float(longitude) <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees.')
        dataset = self._dataset(next(iter(self.dataset_paths)))
        for name, value in (('latitude', filters.get('min_lat')), ('latitude', filters.get('max_lat')), ('longitude', filters.get('min_lon')), ('longitude', filters.get('max_lon'))):
            if value is None:
                continue
            coordinate = self._coordinate_name(dataset, name)
            values = dataset[coordinate].values
            if float(value) < float(values.min()) or float(value) > float(values.max()):
                raise LookupError('Requested coordinates are outside the available dataset coverage.')
        for name, value in (('depth', filters.get('depth')), ('time', filters.get('timestamp'))):
            if value is None:
                continue
            coordinate = self._coordinate_name(dataset, name)
            values = dataset[coordinate].values
            index = self._nearest_index(values, value)
            distance = abs(float(values[index]) - float(value)) if name == 'depth' else abs(self._normalize_datetime(values[index]) - self._normalize_datetime(value)).total_seconds()
            if (name == 'depth' and (float(value) < float(values.min()) or float(value) > float(values.max()))) or (name == 'time' and (self._normalize_datetime(value) < self._normalize_datetime(values.min()) or self._normalize_datetime(value) > self._normalize_datetime(values.max()))):
                raise LookupError(f'Requested {name} is outside the available dataset range.')

    def _nearest_record(self, dataset: Any, fields: tuple[str, ...], latitude: float, longitude: float, depth: float, timestamp: str | datetime) -> dict[str, Any]:
        return min(
            [item for item in self.get_ocean_records(parameter=None, depth=depth, timestamp=timestamp)],
            key=lambda item: abs(item['latitude'] - latitude) + abs(item['longitude'] - longitude),
        )

    def _select_coordinates(self, dataset: Any, **filters: Any) -> dict[str, Any]:
        selected: dict[str, Any] = {}
        for name in self.COORDINATE_NAMES:
            coordinate_name = self._coordinate_name(dataset, name)
            values = dataset[coordinate_name].values
            if name == 'depth':
                requested = filters['depth']
                indices = [self._nearest_index(values, requested)] if requested is not None else list(range(len(values)))
            elif name == 'time':
                requested = filters['timestamp']
                indices = [self._nearest_index(values, requested)] if requested is not None else list(range(len(values)))
            else:
                filter_name = 'lat' if name == 'latitude' else 'lon'
                lower = filters[f'min_{filter_name}']
                upper = filters[f'max_{filter_name}']
                indices = [index for index, value in enumerate(values) if (lower is None or value >= lower) and (upper is None or value <= upper)]
            selected[name] = indices
            selected[f'{name}_values'] = values
        return selected

    def _value(self, dataset: Any, field: str, time_value: Any, depth_value: Any, latitude_value: Any, longitude_value: Any) -> float | None:
        data = dataset[self.VARIABLE_FILES[field][1]]
        values = {'time': time_value, 'depth': depth_value, 'latitude': latitude_value, 'longitude': longitude_value}
        indexers = {
            self._coordinate_name(dataset, name): value
            for name, value in values.items()
            if self._coordinate_name(dataset, name, required=False) in data.dims
        }
        try:
            value = data.sel(indexers).item()
            return float(value) if math.isfinite(float(value)) else None
        except (KeyError, TypeError, ValueError):
            return None

    def _coordinate_name(self, dataset: Any, coordinate: str, *, required: bool = True) -> str | None:
        cached = self._coordinate_names_by_dataset.get(id(dataset), {}).get(coordinate)
        if cached is not None:
            return cached
        name = next((candidate for candidate in self.COORDINATE_NAMES[coordinate] if candidate in dataset.coords or candidate in dataset.dims), None)
        if name is None and required:
            raise ValueError(f'NetCDF dataset is missing a {coordinate} coordinate.')
        return name

    @staticmethod
    def _nearest_index(values: Any, requested: Any) -> int:
        if isinstance(requested, (str, datetime)):
            requested = CopernicusNetCDFRepository._normalize_datetime(requested)
            distances = [abs(CopernicusNetCDFRepository._normalize_datetime(value) - requested) for value in values]
        else:
            distances = [abs(float(value) - float(requested)) for value in values]
        return min(range(len(values)), key=distances.__getitem__)

    @staticmethod
    def _normalize_datetime(value: Any) -> datetime:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)

    @classmethod
    def _serialize_timestamp(cls, value: Any) -> str:
        return cls._normalize_datetime(value).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    @staticmethod
    def _unit_for(dataset: Any, field: str) -> str:
        variable = dataset[CopernicusNetCDFRepository.VARIABLE_FILES[field][1]]
        return str(variable.attrs.get('units', ''))

    @staticmethod
    def _current_speed(current_u: float | None, current_v: float | None) -> float | None:
        if current_u is None or current_v is None:
            return None
        return math.sqrt(current_u**2 + current_v**2)