from __future__ import annotations

import logging

from app.core.config import Settings, settings
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
            paths = {}
            for field in {'temperature', 'salinity', 'current_u', 'current_v'}:
                matches = [item.path for item in discovered if item.variable == field]
                if matches:
                    paths[field] = matches
            if not paths:
                raise ValueError('Copernicus data directory contains no valid supported datasets.')
            return CopernicusNetCDFRepository(paths)
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
        return CopernicusNetCDFRepository(paths)
    raise ValueError(f'Unsupported ocean provider: {config.ocean_provider}')