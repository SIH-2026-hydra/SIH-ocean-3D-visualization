from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.schemas import DatasetMetadata, ModelRecord, ObservationRecord
from app.repositories.base import BaseOceanRepository


class JsonOceanRepository(BaseOceanRepository):
    """Loads and validates JSON datasets for the ocean data layer."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or Path(__file__).resolve().parent.parent).resolve()
        self.data_dir = self.base_dir / 'data'

    def _load_json(self, filename: str) -> list[dict[str, Any]]:
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f'Missing dataset file: {filename}')

        try:
            with file_path.open('r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Malformed JSON in {filename}: {exc.msg}') from exc

        if not isinstance(payload, list):
            raise ValueError(f'Dataset {filename} must contain a JSON array.')

        return payload

    def get_model_records(self) -> list[dict[str, Any]]:
        return [
            ModelRecord.model_validate(item).model_dump(mode='json')
            for item in self._load_json('model_data.json')
        ]

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
