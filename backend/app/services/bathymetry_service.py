"""Bathymetry service for static geographic seafloor depth queries."""

from __future__ import annotations

from app.core.config import settings
from app.repositories.base import BaseOceanRepository


class BathymetryService:
    """Service layer for bathymetry (static geographic data)."""

    def __init__(self, repository: BaseOceanRepository) -> None:
        self.repository = repository

    def get_bathymetry_records(self) -> list[dict]:
        """Get all bathymetry records."""
        if not self._repository_ready():
            return []
        return self.repository.get_bathymetry_records()

    def _repository_ready(self) -> bool:
        provider_ready = self.repository.provider_ready
        return provider_ready or not (
            settings.ocean_provider.lower().strip() == 'auto'
            and settings.copernicus_acquisition_enabled
        )

    def filter_records(
        self,
        records: list[dict],
        *,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
    ) -> list[dict]:
        """Filter bathymetry records by geographic bounds."""
        filtered = records

        if min_lat is not None:
            filtered = [r for r in filtered if r['latitude'] >= min_lat]
        if max_lat is not None:
            filtered = [r for r in filtered if r['latitude'] <= max_lat]
        if min_lon is not None:
            filtered = [r for r in filtered if r['longitude'] >= min_lon]
        if max_lon is not None:
            filtered = [r for r in filtered if r['longitude'] <= max_lon]

        return filtered

    def find_nearest_point(self, records: list[dict], lat: float, lon: float) -> dict | None:
        """
        Find the nearest bathymetry record to a given point.
        Returns the matching record or None if no data available.
        """
        if not records:
            return None

        min_distance = float('inf')
        nearest = None

        for record in records:
            # Simple Euclidean distance in lat/lon space (acceptable for small regions)
            dist = (record['latitude'] - lat) ** 2 + (record['longitude'] - lon) ** 2
            if dist < min_distance:
                min_distance = dist
                nearest = record

        return nearest

    @staticmethod
    def is_within_coverage(records: list[dict], lat: float, lon: float) -> bool:
        """Return whether a point is inside this provider's declared record coverage."""
        if not records:
            return False

        latitudes = [float(record['latitude']) for record in records]
        longitudes = [float(record['longitude']) for record in records]
        return min(latitudes) <= lat <= max(latitudes) and min(longitudes) <= lon <= max(longitudes)

    def get_point_bathymetry(self, lat: float, lon: float) -> dict | None:
        """
        Query bathymetry at a specific point.
        Returns the nearest matched record or None if outside coverage.
        """
        records = self.get_bathymetry_records()
        if not self.is_within_coverage(records, lat, lon):
            return None

        nearest = self.find_nearest_point(records, lat, lon)
        if nearest is None or nearest.get('is_land', False):
            return None

        return {
            'requested_location': {'latitude': lat, 'longitude': lon},
            'matched_location': {'latitude': nearest['latitude'], 'longitude': nearest['longitude']},
            'seafloor_depth': nearest['seafloor_depth'],
            'source': nearest['source'],
            'is_synthetic': 'synthetic' in nearest['source'].lower(),
            'is_land': nearest.get('is_land', False),
        }
