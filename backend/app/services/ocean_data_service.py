from __future__ import annotations

import math
from datetime import datetime, timezone

from app.repositories.base import BaseOceanRepository
from app.services.bathymetry_service import BathymetryService
from app.services.derived_products import DERIVED_PRODUCTS, calculate_derived_product


class OceanDataService:
    """Service layer for normalized ocean model queries and future-ready discovery metadata."""

    VALID_PARAMETERS = {'temperature', 'salinity', 'current', *DERIVED_PRODUCTS}
    PARAMETER_TO_FIELD = {
        'temperature': 'temperature',
        'salinity': 'salinity',
        'current': 'current_u',
    }

    def __init__(self, repository: BaseOceanRepository) -> None:
        self.repository = repository

    def get_model_records(self, *, depth: float | None = None) -> list[dict]:
        return self.repository.query_ocean_records(parameter='all', depth=depth)

    def get_observation_records(self, *, depth: float | None = None) -> list[dict]:
        records = self.repository.get_observation_records()
        if depth is not None:
            records = [record for record in records if record['depth'] == depth]
        return records

    def get_dataset_metadata(self) -> list[dict]:
        return self.repository.get_dataset_metadata()

    def get_ocean_discovery(self) -> dict:
        metadata = self.get_dataset_metadata()
        dataset = metadata[0] if metadata else {}
        return {
            'parameters': ['temperature', 'salinity', 'current', *DERIVED_PRODUCTS],
            'units': {
                'temperature': '°C',
                'salinity': 'PSU',
                'depth': 'm',
                'current_u': 'm/s',
                'current_v': 'm/s',
                'current_speed': 'm/s',
                'current_direction': 'degrees',
                'latitude': 'decimal degrees',
                'longitude': 'decimal degrees',
                'time': 'UTC',
            },
            'depths': self._get_available_depths(),
            'timestamps': self.get_available_timestamps(),
            'spatialCoverage': dataset.get('spatial_coverage', {
                'min_latitude': -90.0,
                'max_latitude': 90.0,
                'min_longitude': -180.0,
                'max_longitude': 180.0,
            }),
            'dataset': dataset.get('dataset_id', 'demo-ocean-model'),
            'synthetic': bool(dataset.get('is_synthetic', True)),
            'sourceType': dataset.get('source_type', 'model'),
        }

    def get_available_timestamps(self) -> list[str]:
        capabilities = self.repository.get_provider_capabilities()
        provider_timestamps = capabilities.get('timestamps')
        if provider_timestamps is not None:
            return provider_timestamps
        records = self.repository.query_ocean_records(parameter='all')
        timestamps = sorted({record['timestamp'] for record in records})
        return [value if isinstance(value, str) else value.replace(microsecond=0).isoformat().replace('+00:00', 'Z') for value in timestamps]

    def _get_available_depths(self) -> list[float]:
        provider_depths = self.repository.get_provider_capabilities().get('depths')
        if provider_depths is not None:
            return provider_depths
        return [0.0, 50.0, 100.0, 200.0, 500.0]

    def filter_records(
        self,
        records: list[dict],
        *,
        parameter: str | None = None,
        depth: float | None = None,
        timestamp: str | datetime | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        source: str | None = None,
    ) -> list[dict]:
        filtered = list(records)

        if parameter is not None:
            if parameter not in self.VALID_PARAMETERS:
                raise ValueError(f'Unsupported parameter: {parameter}')

        if depth is not None:
            filtered = [record for record in filtered if float(record['depth']) == float(depth)]

        if timestamp is not None:
            normalized = self._normalize_timestamp(timestamp)
            filtered = [record for record in filtered if self._normalize_timestamp(record['timestamp']) == normalized]

        if min_lat is not None:
            filtered = [record for record in filtered if float(record['latitude']) >= float(min_lat)]
        if max_lat is not None:
            filtered = [record for record in filtered if float(record['latitude']) <= float(max_lat)]
        if min_lon is not None:
            filtered = [record for record in filtered if float(record['longitude']) >= float(min_lon)]
        if max_lon is not None:
            filtered = [record for record in filtered if float(record['longitude']) <= float(max_lon)]

        if source is not None:
            source_value = source.lower()
            filtered = [
                record for record in filtered
                if (record.get('source_type') or record.get('source', 'model')).lower() == source_value
                or record.get('source', '').lower() == source_value
            ]

        return filtered

    def get_ocean_records(
        self,
        *,
        parameter: str = 'temperature',
        depth: float | None = None,
        timestamp: str | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        source: str | None = None,
    ) -> list[dict]:
        if parameter not in self.VALID_PARAMETERS:
            raise ValueError(f'Unsupported parameter: {parameter}')

        records = self.repository.query_ocean_records(
            parameter='current' if parameter in DERIVED_PRODUCTS else parameter,
            depth=depth,
            timestamp=timestamp,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            source=source,
        )

        if parameter in DERIVED_PRODUCTS:
            return [self._serialize_derived_record(record, parameter) for record in records]
        if parameter == 'current':
            return [self._serialize_current_record(record) for record in records]
        return [self._serialize_scalar_record(record, parameter) for record in records]

    def query_ocean_data(
        self,
        *,
        parameter: str = 'temperature',
        depth: float | None = None,
        min_depth: float | None = None,
        max_depth: float | None = None,
        timestamp: str | None = None,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        sampling_factor: int = 1,
        source: str | None = None,
    ) -> tuple[list[dict], dict[str, object]]:
        if min_depth is not None and max_depth is not None and min_depth > max_depth:
            raise ValueError('min_depth cannot be greater than max_depth.')
        if start_time is not None and end_time is not None and self._normalize_timestamp(start_time) > self._normalize_timestamp(end_time):
            raise ValueError('start_time cannot be later than end_time.')
        if sampling_factor < 1:
            raise ValueError('sampling_factor must be greater than or equal to 1.')

        records = self.get_ocean_records(
            parameter=parameter,
            depth=depth,
            timestamp=timestamp,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            source=source,
        )
        if min_depth is not None:
            records = [record for record in records if float(record['depth']) >= min_depth]
        if max_depth is not None:
            records = [record for record in records if float(record['depth']) <= max_depth]
        if start_time is not None:
            start = self._normalize_timestamp(start_time)
            records = [record for record in records if self._normalize_timestamp(record['timestamp']) >= start]
        if end_time is not None:
            end = self._normalize_timestamp(end_time)
            records = [record for record in records if self._normalize_timestamp(record['timestamp']) <= end]
        if sampling_factor > 1:
            records = self._sample_spatial_grid(records, sampling_factor)

        product = DERIVED_PRODUCTS.get(parameter)
        units = {'temperature': '°C', 'salinity': 'PSU', 'current': 'm/s'}
        metadata = {
            'variable': parameter,
            'units': product['units'] if product else units[parameter],
            'gridResolution': self._grid_resolution(records),
            'returnedCellCount': len(records),
            'samplingFactor': sampling_factor,
        }
        if product:
            metadata.update({
                'derivedProduct': product['name'],
                'sourceVariables': list(product['source_variables']),
            })
        return records, metadata

    @staticmethod
    def _sample_spatial_grid(records: list[dict], factor: int) -> list[dict]:
        spatial_points: dict[tuple[float, float], int] = {}
        sampled: list[dict] = []
        for record in records:
            point = (float(record['latitude']), float(record['longitude']))
            point_index = spatial_points.setdefault(point, len(spatial_points))
            if point_index % factor == 0:
                sampled.append(record)
        return sampled

    @staticmethod
    def _grid_resolution(records: list[dict]) -> str:
        dimensions = {
            'latitude': len({record['latitude'] for record in records}),
            'longitude': len({record['longitude'] for record in records}),
            'depth': len({record['depth'] for record in records}),
            'time': len({record['timestamp'] for record in records}),
        }
        return ' x '.join(f'{name}={count}' for name, count in dimensions.items())

    def get_ocean_point(
        self,
        *,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: str | datetime,
    ) -> dict:
        lat = float(latitude)
        lon = float(longitude)
        if not -90.0 <= lat <= 90.0:
            raise ValueError('Latitude must be between -90 and 90 degrees.')
        if not -180.0 <= lon <= 180.0:
            raise ValueError('Longitude must be between -180 and 180 degrees.')
        if float(depth) < 0:
            raise ValueError('Depth must be greater than or equal to 0.')

        metadata = self.get_dataset_metadata()
        coverage = metadata[0].get('spatial_coverage', {}) if metadata else {}
        min_lat = coverage.get('min_latitude', -90.0)
        max_lat = coverage.get('max_latitude', 90.0)
        min_lon = coverage.get('min_longitude', -180.0)
        max_lon = coverage.get('max_longitude', 180.0)
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            raise LookupError('Requested point is outside the available demo coverage.')

        # Bathymetry remains a separate provider, but it supplies local validity
        # constraints when coverage is available. This avoids fabricating values
        # below the seafloor while allowing either provider to be replaced later.
        bathymetry = BathymetryService(self.repository).get_point_bathymetry(lat, lon)
        if bathymetry and float(depth) > float(bathymetry['seafloor_depth']):
            raise ValueError(
                f"Requested depth is below the local seafloor ({bathymetry['seafloor_depth']:.0f} m)."
            )

        matched = self.repository.query_ocean_point(latitude=lat, longitude=lon, depth=float(depth), timestamp=timestamp)
        return self._build_point_response(lat, lon, matched)

    def _build_point_response(self, latitude: float, longitude: float, matched: dict) -> dict:
        return {
            'requestedLocation': {'latitude': latitude, 'longitude': longitude},
            'matchedLocation': {
                'latitude': float(matched['latitude']),
                'longitude': float(matched['longitude']),
                'depth': float(matched['depth']),
                'timestamp': self._serialize_timestamp(matched['timestamp']),
            },
            'depth': float(matched['depth']),
            'timestamp': self._serialize_timestamp(matched['timestamp']),
            'model': {
                'temperature': matched.get('temperature'),
                'salinity': matched.get('salinity'),
                'currentU': matched.get('current_u'),
                'currentV': matched.get('current_v'),
                'currentSpeed': self._current_speed(matched.get('current_u'), matched.get('current_v')),
            },
            'observation': None,
            'prediction': None,
            'source': {
                'datasetId': matched.get('dataset_id'),
                'sourceType': matched.get('source_type', 'model'),
                'source': matched.get('source', 'demo-synthetic-model'),
                'isSynthetic': bool(matched.get('is_synthetic', True)),
            },
        }

    def _serialize_scalar_record(self, record: dict, parameter: str) -> dict:
        value = record.get(parameter)
        return {
            'latitude': float(record['latitude']),
            'longitude': float(record['longitude']),
            'depth': float(record['depth']),
            'timestamp': self._serialize_timestamp(record['timestamp']),
            'value': value,
        }

    def _serialize_current_record(self, record: dict) -> dict:
        current_u = record.get('current_u')
        current_v = record.get('current_v')
        return {
            'latitude': float(record['latitude']),
            'longitude': float(record['longitude']),
            'depth': float(record['depth']),
            'timestamp': self._serialize_timestamp(record['timestamp']),
            'current_u': current_u,
            'current_v': current_v,
            'speed': self._current_speed(current_u, current_v),
        }

    def _serialize_derived_record(self, record: dict, product: str) -> dict:
        return {
            'latitude': float(record['latitude']),
            'longitude': float(record['longitude']),
            'depth': float(record['depth']),
            'timestamp': self._serialize_timestamp(record['timestamp']),
            'value': calculate_derived_product(product, record),
        }

    @staticmethod
    def _serialize_timestamp(value: str | datetime) -> str:
        if isinstance(value, datetime):
            dt = value
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        if value.endswith('Z'):
            return value
        return datetime.fromisoformat(value).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    @staticmethod
    def _normalize_timestamp(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _current_speed(current_u: float | None, current_v: float | None) -> float | None:
        if current_u is None or current_v is None:
            return None
        return math.sqrt(float(current_u) ** 2 + float(current_v) ** 2)

