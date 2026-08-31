from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseOceanRepository(ABC):
    """Abstract repository contract for ocean datasets."""

    @abstractmethod
    def get_model_records(self) -> list[dict[str, Any]]:
        """Return normalized model records without endpoint-specific filtering."""

    @abstractmethod
    def get_observation_records(self) -> list[dict[str, Any]]:
        """Return normalized observation records without endpoint-specific filtering."""

    @abstractmethod
    def get_dataset_metadata(self) -> list[dict[str, Any]]:
        """Return dataset metadata records."""
