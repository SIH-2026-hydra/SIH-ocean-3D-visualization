from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelRecord(BaseModel):
    """Normalized numerical model output record."""

    model_config = ConfigDict(populate_by_name=True)

    model_id: str
    dataset_id: str
    timestamp: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    depth: float = Field(ge=0.0)
    temperature: float | None = None
    salinity: float | None = None
    current_u: float | None = None
    current_v: float | None = None
    source: str = 'synthetic-model'

    @field_validator('timestamp')
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ObservationRecord(BaseModel):
    """Normalized in-situ observation record."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    station_id: str
    dataset_id: str
    timestamp: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    depth: float = Field(ge=0.0)
    temperature: float | None = None
    salinity: float | None = None
    current_u: float | None = None
    current_v: float | None = None
    source_type: str
    source_name: str
    quality_flag: str = 'demo'

    @field_validator('timestamp')
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class DatasetMetadata(BaseModel):
    """Metadata describing a dataset used by the frontend and API consumers."""

    dataset_id: str
    dataset_name: str
    description: str
    source: str
    source_type: str
    spatial_coverage: dict[str, Any]
    time_range: dict[str, str]
    resolution: str
    variables: list[str]
    units: dict[str, str]
    last_updated: str
    is_synthetic: bool = True
