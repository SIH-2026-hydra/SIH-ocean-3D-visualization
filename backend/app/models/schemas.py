from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelRecord(BaseModel):
    """Normalized numerical model output record."""

    model_config = ConfigDict(populate_by_name=True)

    model_id: str | None = None
    dataset_id: str
    source_type: str = 'model'
    source: str = 'demo-synthetic-model'
    timestamp: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    depth: float = Field(ge=0.0)
    temperature: float | None = None
    salinity: float | None = None
    current_u: float | None = None
    current_v: float | None = None

    @field_validator('timestamp')
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ObservationRecord(BaseModel):
    """Normalized in-situ observation record."""

    model_config = ConfigDict(populate_by_name=True)

    observation_id: str
    platform_id: str
    platform_type: str
    dataset_id: str
    timestamp: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    depth: float = Field(ge=0.0)
    temperature: float | None = None
    salinity: float | None = None
    current_u: float | None = None
    current_v: float | None = None
    quality: str = 'demo'
    source: str = 'demo-synthetic-observations'
    is_synthetic: bool = True

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


class BathymetryRecord(BaseModel):
    """Static geographic bathymetry/seafloor depth record (no time/depth dependence)."""

    model_config = ConfigDict(populate_by_name=True)

    bathymetry_id: str | None = None
    dataset_id: str
    source_type: str = 'bathymetry'
    source: str = 'demo-synthetic-bathymetry'
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    seafloor_depth: float = Field(ge=0.0)
    is_land: bool = False


class PredictionRecord(BaseModel):
    """ML prediction output record."""

    model_config = ConfigDict(populate_by_name=True)

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    depth: float = Field(ge=0.0)
    timestamp: datetime
    temperature: float | None = None
    salinity: float | None = None
    current_u: float | None = None
    current_v: float | None = None
    current_speed: float | None = Field(default=None, ge=0.0)
    model_id: str = 'prototype-predictor-v1'
    model_version: str = '1.0'
    prediction_type: str = 'prototype'
    source: str = 'prototype-ml-prediction'
    is_experimental: bool = True

    @field_validator('timestamp')
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ApiRecord(BaseModel):
    """Flexible API record preserving provider-specific response fields."""

    model_config = ConfigDict(extra='allow')


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiErrorResponse(BaseModel):
    detail: str
    error: ApiError


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    provider_ready: bool
    registry_ready: bool


RecordType = TypeVar('RecordType')


class DataResponse(BaseModel, Generic[RecordType]):
    data: list[RecordType]


class CountedDataResponse(DataResponse[ApiRecord]):
    count: int
    total: int | None = None


class ModelResponse(DataResponse[ApiRecord]):
    metadata: dict[str, Any]


class OceanResponse(BaseModel):
    query: dict[str, Any]
    metadata: dict[str, Any]
    data: list[ApiRecord]


class OceanPointResponse(ApiRecord):
    """Point response preserving the established camelCase payload."""


class ObservationResponse(DataResponse[ApiRecord]):
    metadata: dict[str, Any]


class PointObservationResponse(BaseModel):
    available: bool
    requested_location: dict[str, float]
    requested_depth: float
    requested_time: str
    observation: ApiRecord | None


class PredictionResponse(BaseModel):
    requested_location: dict[str, float]
    requested_depth: float
    requested_time: str
    available: bool
    unavailable_reason: str | None
    prediction: ApiRecord | None


class MetadataResponse(BaseModel):
    metadata: dict[str, Any]
    discovery: dict[str, Any]
    data: list[ApiRecord]
