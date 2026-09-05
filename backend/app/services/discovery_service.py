from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.models.dataset_bundle import DatasetBundle
from app.repositories.base import BaseOceanRepository
from app.services.derived_products import DERIVED_PRODUCTS


class DiscoveryService:
    """Translate repository-owned DatasetBundles into public discovery data."""

    RAW_VARIABLES = {
        'temperature': {'display_name': 'Temperature', 'units': 'degC'},
        'salinity': {'display_name': 'Salinity', 'units': 'PSU'},
        'current_u': {'display_name': 'Eastward current', 'units': 'm/s'},
        'current_v': {'display_name': 'Northward current', 'units': 'm/s'},
    }

    def __init__(self, repository: BaseOceanRepository) -> None:
        self.repository = repository

    def dataset_bundles(self) -> tuple[DatasetBundle, ...]:
        if not self._provider_ready():
            return ()
        bundles = getattr(self.repository, 'dataset_bundles', ())
        return tuple(bundle for bundle in bundles if isinstance(bundle, DatasetBundle))

    def catalog(self) -> list[dict[str, Any]]:
        return [self._serialize_bundle(bundle) for bundle in self.dataset_bundles()]

    def variables(self) -> list[dict[str, Any]]:
        available = {variable for bundle in self.dataset_bundles() for variable in bundle.available_variables}
        variables = []
        for variable, definition in self.RAW_VARIABLES.items():
            if not available or variable in available:
                variables.append(self._variable(variable, definition, False, ()))
        variables.extend(
            self._variable(name, definition, True, definition['source_variables'])
            for name, definition in DERIVED_PRODUCTS.items()
        )
        return variables

    def coverage(self) -> list[dict[str, Any]]:
        return [
            {
                'dataset_id': bundle.dataset_id,
                'spatial_coverage': dict(bundle.spatial_coverage),
                'temporal_coverage': dict(bundle.temporal_coverage),
                'depth_range': {
                    'min': min(bundle.available_depths) if bundle.available_depths else None,
                    'max': max(bundle.available_depths) if bundle.available_depths else None,
                },
            }
            for bundle in self.dataset_bundles()
        ]

    def capabilities(self) -> dict[str, Any]:
        providers = sorted({bundle.provider for bundle in self.dataset_bundles()})
        if not providers:
            providers = self._configured_providers()
        return {
            'query_types': ['viewport', 'point'],
            'interval_queries': {'depth': True, 'time': True},
            'sampling': True,
            'derived_products': list(DERIVED_PRODUCTS),
            'supported_providers': providers,
            'runtime': {
                'mode': 'request-driven' if settings.copernicus_acquisition_enabled else 'configured-provider',
                'provider_ready': self._provider_ready(),
                'acquisition_available': settings.copernicus_acquisition_enabled,
                'cache_directory': settings.copernicus_cache_dir,
            },
            'operational_region': {
                'min_latitude': settings.copernicus_operational_min_latitude,
                'max_latitude': settings.copernicus_operational_max_latitude,
                'min_longitude': settings.copernicus_operational_min_longitude,
                'max_longitude': settings.copernicus_operational_max_longitude,
            },
        }

    def _provider_ready(self) -> bool:
        """Avoid dereferencing the request-driven repository before a query binds it."""
        return bool(getattr(self.repository, 'provider_ready', True))

    @staticmethod
    def _configured_providers() -> list[str]:
        provider = settings.ocean_provider.lower().strip()
        if provider in {'auto', 'copernicus'}:
            return ['Copernicus Marine']
        return [provider.upper()]

    @staticmethod
    def _serialize_bundle(bundle: DatasetBundle) -> dict[str, Any]:
        return {
            'dataset_id': bundle.dataset_id,
            'provider': bundle.provider,
            'product': bundle.product,
            'model': bundle.model,
            'forecast_cycle': bundle.forecast_cycle,
            'available_variables': list(bundle.available_variables),
            'spatial_coverage': dict(bundle.spatial_coverage),
            'temporal_coverage': dict(bundle.temporal_coverage),
            'available_depth_levels': list(bundle.available_depths),
            'metadata': dict(bundle.metadata),
        }

    @staticmethod
    def _variable(name: str, definition: dict[str, Any], derived: bool, source_variables: tuple[str, ...]) -> dict[str, Any]:
        return {
            'variable_name': name,
            'display_name': definition.get('name', definition.get('display_name', name)),
            'units': definition.get('units', ''),
            'is_derived': derived,
            'source_variables': list(source_variables),
            'supports_spatial_queries': True,
            'supports_temporal_queries': True,
        }
