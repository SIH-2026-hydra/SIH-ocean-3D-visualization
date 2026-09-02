from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.schemas import BathymetryRecord, DatasetMetadata, ModelRecord, ObservationRecord
from app.models.dataset_bundle import DatasetBundle
from app.repositories.base import BaseOceanRepository
from app.repositories.exceptions import DatasetUnavailableError, InvalidProviderQueryError


class JsonOceanRepository(BaseOceanRepository):
    """Loads and validates JSON datasets for the ocean data layer."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or Path(__file__).resolve().parent.parent).resolve()
        self.data_dir = self.base_dir / 'data'
        self.dataset_bundles = (
            DatasetBundle(
                dataset_id='demo-indian-ocean-model',
                provider='JSON',
                product='OCEANX DEMO JSON MODEL',
                model='Deterministic Synthetic Ocean Model',
                forecast_cycle='2026-08-24T00:00:00Z',
                variables=('temperature', 'salinity', 'current_u', 'current_v'),
                coordinate_signature=(
                    ('time', 'timestamp'),
                    ('depth', 'depth'),
                    ('latitude', 'latitude'),
                    ('longitude', 'longitude'),
                ),
                spatial_coverage={
                    'min_latitude': 5.0,
                    'max_latitude': 30.0,
                    'min_longitude': 45.0,
                    'max_longitude': 95.0,
                },
                temporal_coverage={
                    'start': '2026-08-24T00:00:00Z',
                    'end': '2026-08-24T20:00:00Z',
                },
                depth_levels=(0.0, 50.0, 100.0, 200.0, 500.0),
                source_files={'model': (self.data_dir / 'model_data.json',)},
                metadata={
                    'source_type': 'model',
                    'is_synthetic': True,
                    'dataset_name': 'Indian Ocean Demo Model',
                },
            ),
        )

    def _load_json(self, filename: str) -> list[dict[str, Any]]:
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise DatasetUnavailableError(f'Missing dataset file: {filename}')

        try:
            with file_path.open('r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise DatasetUnavailableError(f'Malformed JSON in {filename}: {exc.msg}') from exc

        if not isinstance(payload, list):
            raise DatasetUnavailableError(f'Dataset {filename} must contain a JSON array.')

        return payload

    def get_model_records(self) -> list[dict[str, Any]]:
        return [
            ModelRecord.model_validate(item).model_dump(mode='json')
            for item in self._load_json('model_data.json')
        ]

    def query_ocean_records(
        self,
        *,
        parameter: str = 'temperature',
        depth: float | None = None,
        timestamp: str | datetime | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        if parameter not in {'temperature', 'salinity', 'current', 'all'}:
            raise InvalidProviderQueryError(f'Unsupported parameter: {parameter}')
        records = self.get_model_records()
        if depth is not None:
            records = [record for record in records if float(record['depth']) == float(depth)]
        if timestamp is not None:
            normalized = self._normalize_timestamp(timestamp)
            records = [record for record in records if self._normalize_timestamp(record['timestamp']) == normalized]
        for field, lower, upper in (
            ('latitude', min_lat, max_lat),
            ('longitude', min_lon, max_lon),
        ):
            if lower is not None:
                records = [record for record in records if float(record[field]) >= float(lower)]
            if upper is not None:
                records = [record for record in records if float(record[field]) <= float(upper)]
        if source is not None:
            source_value = source.lower()
            records = [
                record for record in records
                if (record.get('source_type') or record.get('source', 'model')).lower() == source_value
                or record.get('source', '').lower() == source_value
            ]
        return records

    def query_ocean_point(
        self,
        *,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: str | datetime,
    ) -> dict[str, Any]:
        records = self.get_model_records()
        time_value = self._normalize_timestamp(timestamp)
        candidates = [record for record in records if float(record['depth']) == float(depth)]
        if not candidates:
            candidates = records
        timed = [record for record in candidates if self._normalize_timestamp(record['timestamp']) == time_value]
        if timed:
            candidates = timed
        if not candidates:
            raise LookupError('No ocean model data available for the requested point.')
        return min(
            candidates,
            key=lambda record: (
                abs(float(record['latitude']) - float(latitude)),
                abs(float(record['longitude']) - float(longitude)),
                abs(float(record['depth']) - float(depth)),
            ),
        )

    def get_provider_capabilities(self) -> dict[str, Any]:
        metadata = self.get_dataset_metadata()
        return {
            'provider': 'JSON',
            'available_parameters': ['temperature', 'salinity', 'current'],
            'metadata': metadata,
            'depths': [0.0, 50.0, 100.0, 200.0, 500.0],
        }

    def health(self) -> dict[str, Any]:
        try:
            self.get_dataset_metadata()
        except (FileNotFoundError, ValueError) as exc:
            return {'available': False, 'provider': 'JSON', 'error': str(exc)}
        return {'available': True, 'provider': 'JSON'}

    def close(self) -> None:
        return None

    @staticmethod
    def _normalize_timestamp(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            result = value
        else:
            result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)

    def get_observation_records(self) -> list[dict[str, Any]]:
        return [
            ObservationRecord.model_validate(item).model_dump(mode='json')
            for item in self._load_json('observations.json')
        ]

    def get_dataset_metadata(self) -> list[dict[str, Any]]:
        return [
            DatasetMetadata.model_validate(item).model_dump(mode='json')
            for item in self._load_json('datasets.json')
        ]

    def get_bathymetry_records(self) -> list[dict[str, Any]]:
        return [
            BathymetryRecord.model_validate(item).model_dump(mode='json')
            for item in self._load_json('bathymetry.json')
        ]
