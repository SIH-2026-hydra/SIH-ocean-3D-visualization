from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseOceanRepository(ABC):
    """Explicit provider contract used by all backend data providers."""

    @property
    def provider_ready(self) -> bool:
        """Concrete providers are ready; deferred runtime wrappers override this."""
        return True

    @abstractmethod
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
        """Return normalized model records for a provider query."""

    @abstractmethod
    def query_ocean_point(
        self,
        *,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: str | datetime,
    ) -> dict[str, Any]:
        """Return one normalized model record for a point query."""

    @abstractmethod
    def get_provider_capabilities(self) -> dict[str, Any]:
        """Return provider capabilities and available model dimensions."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return provider health information without raising on normal status."""

    @abstractmethod
    def close(self) -> None:
        """Release provider resources."""

    @abstractmethod
    def get_model_records(self) -> list[dict[str, Any]]:
        """Return normalized model records without endpoint-specific filtering."""

    @abstractmethod
    def get_observation_records(self) -> list[dict[str, Any]]:
        """Return normalized observation records without endpoint-specific filtering."""

    @abstractmethod
    def get_dataset_metadata(self) -> list[dict[str, Any]]:
        """Return dataset metadata records."""

    @abstractmethod
    def get_bathymetry_records(self) -> list[dict[str, Any]]:
        """Return bathymetry records (static geographic data)."""
