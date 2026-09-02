from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DatasetCatalogEntry(BaseModel):
    dataset_id: str
    provider: str
    product: str
    model: str
    forecast_cycle: str | None
    available_variables: list[str]
    spatial_coverage: dict[str, float]
    temporal_coverage: dict[str, str]
    available_depth_levels: list[float]
    metadata: dict[str, Any]


class CatalogResponse(BaseModel):
    datasets: list[DatasetCatalogEntry]


class VariableDiscovery(BaseModel):
    variable_name: str
    display_name: str
    units: str
    is_derived: bool
    source_variables: list[str]
    supports_spatial_queries: bool
    supports_temporal_queries: bool


class VariableResponse(BaseModel):
    variables: list[VariableDiscovery]


class CoverageEntry(BaseModel):
    dataset_id: str
    spatial_coverage: dict[str, float]
    temporal_coverage: dict[str, str]
    depth_range: dict[str, float | None]


class CoverageResponse(BaseModel):
    coverage: list[CoverageEntry]


class CapabilityResponse(BaseModel):
    capabilities: dict[str, Any] = Field(default_factory=dict)
