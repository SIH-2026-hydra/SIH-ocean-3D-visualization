from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import Settings, settings
from app.models.dataset_bundle import DatasetBundle
from app.repositories.base import BaseOceanRepository
from app.repositories.copernicus_netcdf_repository import CopernicusNetCDFRepository
from app.repositories.json_repository import JsonOceanRepository
from app.repositories.netcdf_registry import NetCDFDatasetRegistry
from app.repositories.noaa_repository import NOAAOceanRepository

logger = logging.getLogger(__name__)


def create_repository(config: Settings = settings) -> BaseOceanRepository:
    """Create the configured model repository without coupling API modules to providers."""
    provider = config.ocean_provider.lower().strip()
    logger.info('Selecting ocean provider: %s', provider)
    if provider == 'auto':
        repository = _create_local_copernicus_repository(config, required=False)
        if repository is not None:
            logger.info('Using locally discovered Copernicus Marine dataset(s) for the operational provider.')
            return repository
        logger.warning('No valid local Copernicus dataset was found; using the JSON development provider.')
        return JsonOceanRepository()
    if provider == 'json':
        return JsonOceanRepository()
    if provider == 'noaa':
        return NOAAOceanRepository()
    if provider == 'copernicus':
        repository = _create_local_copernicus_repository(config, required=True)
        assert repository is not None
        return repository
    raise ValueError(f'Unsupported ocean provider: {config.ocean_provider}')


def _create_local_copernicus_repository(config: Settings, *, required: bool) -> CopernicusNetCDFRepository | None:
    """Construct a Copernicus provider only when a usable local source exists."""
    if config.copernicus_data_dir:
        registry = NetCDFDatasetRegistry(config.copernicus_data_dir, pattern=config.copernicus_file_pattern)
        discovered = registry.discover() if config.copernicus_validate_on_startup else []
        logger.info('NetCDF registry ready: directory=%s datasets=%d', config.copernicus_data_dir, len(discovered))
        if discovered:
            repository = CopernicusNetCDFRepository(discovered)
            repository.registry = registry
            return repository
        if required:
            raise ValueError('Copernicus data directory contains no valid supported datasets.')
        return None

    paths = {
        field: path
        for field, path in {
            'temperature': config.copernicus_temperature_path,
            'salinity': config.copernicus_salinity_path,
            'current_u': config.copernicus_current_u_path,
            'current_v': config.copernicus_current_v_path,
        }.items()
        if path and Path(path).is_file()
    }
    if paths:
        return CopernicusNetCDFRepository(_bundle_from_paths(paths))
    if required:
        raise ValueError('Copernicus provider requires at least one valid configured NetCDF path.')
    return None


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
