from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseOceanRepository(ABC):
    """Abstract repository contract for ocean datasets."""

    @abstractmethod
    def get_model_records(self, *, depth: float | None = None) -> list[dict[str, Any]]:
        """Return normalized model records, optionally filtered by depth."""

    @abstractmethod
    def get_observation_records(self, *, depth: float | None = None) -> list[dict[str, Any]]:
        """Return normalized observation records, optionally filtered by depth."""

    @abstractmethod
    def get_dataset_metadata(self) -> list[dict[str, Any]]:
        """Return dataset metadata records."""
