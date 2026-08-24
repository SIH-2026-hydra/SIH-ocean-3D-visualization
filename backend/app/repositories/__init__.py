"""Repository implementations for ocean data access."""

from .base import BaseOceanRepository
from .json_repository import JsonOceanRepository

__all__ = ['BaseOceanRepository', 'JsonOceanRepository']
