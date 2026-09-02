from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import Settings, settings
from app.models.dataset_bundle import DatasetBundle
from app.repositories.base import BaseOceanRepository
from app.repositories.copernicus_netcdf_repository import CopernicusNetCDFRepository
from app.repositories.json_repository import JsonOceanRepository
from app.repositories.netcdf_registry import NetCDFDatasetRegistry

logger = logging.getLogger(__name__)


def create_repository(config: Settings = settings) -> BaseOceanRepository:
    """Create the configured model repository without coupling API modules to providers."""
    provider = config.ocean_provider.lower().strip()
    logger.info('Selecting ocean provider: %s', provider)
    if provider == 'json':
        return JsonOceanRepository()
    if provider == 'copernicus':
        if config.copernicus_data_dir:
            registry = NetCDFDatasetRegistry(config.copernicus_data_dir, pattern=config.copernicus_file_pattern)
            discovered = registry.discover() if config.copernicus_validate_on_startup else []
            logger.info('NetCDF registry ready: directory=%s datasets=%d', config.copernicus_data_dir, len(discovered))
            bundles = discovered
            if not bundles:
                raise ValueError('Copernicus data directory contains no valid supported datasets.')
            repository = CopernicusNetCDFRepository(bundles)
            repository.registry = registry
            return repository
        paths = {
            field: path
            for field, path in {
                'temperature': config.copernicus_temperature_path,
                'salinity': config.copernicus_salinity_path,
                'current_u': config.copernicus_current_u_path,
                'current_v': config.copernicus_current_v_path,
            }.items()
            if path
        }
        if not paths:
            raise ValueError('Copernicus provider requires at least one configured NetCDF path.')
        return CopernicusNetCDFRepository(_bundle_from_paths(paths))
    raise ValueError(f'Unsupported ocean provider: {config.ocean_provider}')


def _bundle_from_paths(paths: dict[str, str]) -> DatasetBundle:
    return DatasetBundle(
        dataset_id='copernicus-global-analysisforecast-phy-001-024',
        provider='Copernicus Marine',
        product='GLOBAL_ANALYSISFORECAST_PHY_001_024',
        model='Mercator Ocean GLO12',
        forecast_cycle=None,
        variables=tuple(paths),
        coordinate_signature=(),
        spatial_coverage={},
        temporal_coverage={},
        depth_levels=(),
        source_files={field: (Path(value),) for field, value in paths.items()},
        metadata={},
    )