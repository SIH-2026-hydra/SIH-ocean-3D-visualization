"""Repository implementations for ocean data access."""

from .base import BaseOceanRepository
from .copernicus_netcdf_repository import CopernicusNetCDFRepository
from .exceptions import (
	DataUnavailableError,
	DatasetUnavailableError,
	InvalidProviderQueryError,
	ProviderError,
	ProviderUnavailableError,
	UnsupportedProviderOperationError,
)
from .factory import create_repository
from .json_repository import JsonOceanRepository
from .netcdf_registry import DatasetDescriptor, NetCDFDatasetRegistry
from app.models.dataset_bundle import DatasetBundle

__all__ = [
	'BaseOceanRepository',
	'CopernicusNetCDFRepository',
	'DataUnavailableError',
	'DatasetBundle',
	'DatasetDescriptor',
	'DatasetUnavailableError',
	'InvalidProviderQueryError',
	'JsonOceanRepository',
	'NetCDFDatasetRegistry',
	'ProviderError',
	'ProviderUnavailableError',
	'UnsupportedProviderOperationError',
	'create_repository',
]
