"""Repository implementations for ocean data access."""

from .base import BaseOceanRepository
from .copernicus_netcdf_repository import CopernicusNetCDFRepository
from .factory import create_repository
from .json_repository import JsonOceanRepository
from .netcdf_registry import DatasetDescriptor, NetCDFDatasetRegistry

__all__ = ['BaseOceanRepository', 'CopernicusNetCDFRepository', 'DatasetDescriptor', 'JsonOceanRepository', 'NetCDFDatasetRegistry', 'create_repository']
