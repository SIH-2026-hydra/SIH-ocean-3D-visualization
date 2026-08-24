from __future__ import annotations

from app.repositories.base import BaseOceanRepository


class OceanDataService:
    """Thin service layer for data retrieval and filtering."""

    def __init__(self, repository: BaseOceanRepository) -> None:
        self.repository = repository

    def get_model_records(self, *, depth: float | None = None) -> list[dict]:
        return self.repository.get_model_records(depth=depth)

    def get_observation_records(self, *, depth: float | None = None) -> list[dict]:
        return self.repository.get_observation_records(depth=depth)

    def get_dataset_metadata(self) -> list[dict]:
        return self.repository.get_dataset_metadata()
