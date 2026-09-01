"""Service layer for static in-situ observation records."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.repositories.base import BaseOceanRepository


class ObservationService:
    """Queries normalized measurements without inventing missing observations."""

    MAX_DISTANCE_DEGREES = 3.0
    MAX_TIME_DELTA = timedelta(hours=2)
    MAX_DEPTH_DELTA_METERS = 75.0
    VALID_PARAMETERS = {'temperature', 'salinity', 'current'}

    def __init__(self, repository: BaseOceanRepository) -> None:
        self.repository = repository

    def get_records(
        self,
        *,
        depth: float | None = None,
        timestamp: datetime | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        parameter: str | None = None,
        platform_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if parameter is not None and parameter not in self.VALID_PARAMETERS:
            raise ValueError(f'Unsupported observation parameter: {parameter}')

        records = self.repository.get_observation_records()
        if depth is not None:
            records = [record for record in records if float(record['depth']) == depth]
        if timestamp is not None:
            records = [record for record in records if self.normalize_timestamp(record['timestamp']) == timestamp]
        if min_lat is not None:
            records = [record for record in records if float(record['latitude']) >= min_lat]
        if max_lat is not None:
            records = [record for record in records if float(record['latitude']) <= max_lat]
        if min_lon is not None:
            records = [record for record in records if float(record['longitude']) >= min_lon]
        if max_lon is not None:
            records = [record for record in records if float(record['longitude']) <= max_lon]
        if platform_type is not None:
            records = [record for record in records if record['platform_type'] == platform_type]
        if parameter == 'temperature':
            records = [record for record in records if record.get('temperature') is not None]
        if parameter == 'salinity':
            records = [record for record in records if record.get('salinity') is not None]
        if parameter == 'current':
            records = [record for record in records if record.get('current_u') is not None or record.get('current_v') is not None]
        return records

    def find_nearest(self, *, latitude: float, longitude: float, depth: float, timestamp: datetime) -> dict[str, Any] | None:
        candidates = []
        for record in self.repository.get_observation_records():
            distance = ((float(record['latitude']) - latitude) ** 2 + (float(record['longitude']) - longitude) ** 2) ** 0.5
            time_delta = abs(self.normalize_timestamp(record['timestamp']) - timestamp)
            depth_delta = abs(float(record['depth']) - depth)
            if distance <= self.MAX_DISTANCE_DEGREES and time_delta <= self.MAX_TIME_DELTA and depth_delta <= self.MAX_DEPTH_DELTA_METERS:
                candidates.append((distance, time_delta.total_seconds(), depth_delta, record))
        if not candidates:
            return None
        return min(candidates, key=lambda candidate: candidate[:3])[3]

    @staticmethod
    def normalize_timestamp(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            result = value
        else:
            result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
