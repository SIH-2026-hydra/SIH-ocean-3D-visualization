"""On-demand lifecycle management for locally cached Copernicus datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Callable

from app.acquisition import AcquisitionManager, ScientificAcquisitionRequest
from app.models.dataset_bundle import DatasetBundle
from app.repositories.exceptions import DatasetUnavailableError
from app.repositories.netcdf_registry import NetCDFDatasetRegistry
from app.services.operational_cache import OperationalCacheIndex

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperationalDataRequest:
    """The smallest scientific subset needed to satisfy one query."""

    variables: tuple[str, ...]
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    product: str = 'physical-forecast'
    start_time: str | None = None
    end_time: str | None = None
    min_depth: float | None = None
    max_depth: float | None = None
    resolution: str | None = None
    forecast_cycle: str | None = None
    provider: str = 'Copernicus Marine'


@dataclass(frozen=True)
class DatasetResolution:
    bundles: tuple[DatasetBundle, ...]
    cache_hit: bool


class OperationalDataManager:
    """Resolve cache hits or acquire, validate, and register missing subsets."""

    def __init__(
        self,
        cache_dir: str | Path,
        *,
        acquisition_manager: AcquisitionManager | None = None,
        on_registered: Callable[[], None] | None = None,
        on_available: Callable[[], None] | None = None,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry = NetCDFDatasetRegistry(self.cache_dir)
        self.cache_index = OperationalCacheIndex(self.cache_dir)
        self.acquisition_manager = acquisition_manager or AcquisitionManager.default()
        self.on_registered = on_registered
        self.on_available = on_available
        self._discovered = False

    def ensure_query(
        self,
        *,
        parameter: str,
        min_latitude: float | None,
        max_latitude: float | None,
        min_longitude: float | None,
        max_longitude: float | None,
        timestamp: str | None,
        depth: float | None = None,
        min_depth: float | None = None,
        max_depth: float | None = None,
        resolution: str | None = None,
    ) -> DatasetResolution:
        fields = {'current': ('current_u', 'current_v'), 'current_speed': ('current_u', 'current_v'), 'current_direction': ('current_u', 'current_v')}
        variables = fields.get(parameter, (parameter,))
        bounds = (min_latitude, max_latitude, min_longitude, max_longitude)
        if any(value is None for value in bounds):
            raise ValueError('Operational acquisition requires explicit viewport bounds.')
        return self.ensure(OperationalDataRequest(
            variables=variables,
            min_latitude=float(min_latitude),
            max_latitude=float(max_latitude),
            min_longitude=float(min_longitude),
            max_longitude=float(max_longitude),
            start_time=timestamp,
            end_time=timestamp,
            min_depth=depth if depth is not None else min_depth,
            max_depth=depth if depth is not None else max_depth,
            resolution=resolution,
        ))

    def ensure(self, request: OperationalDataRequest) -> DatasetResolution:
        self._discover()
        cached = self._matching_bundles(request)
        if cached:
            logger.info('Operational cache hit: %s', OperationalCacheIndex.identity(request))
            # A restored cache can satisfy the first request after startup
            # without registering a new bundle.  Make its data queryable
            # before returning control to OceanDataService.
            if self.on_available is not None:
                self.on_available()
                logger.info('Cached operational dataset is available to the active repository.')
            return DatasetResolution(tuple(cached), cache_hit=True)

        logger.info('Operational cache miss: %s', OperationalCacheIndex.identity(request))
        logger.info('Scientific acquisition started: provider=%s variables=%s', request.provider, ','.join(request.variables))
        paths = tuple(Path(path) for path in self.acquisition_manager.acquire(self._scientific_request(request), self.cache_dir))
        if not paths:
            raise DatasetUnavailableError('Copernicus acquisition completed without producing a NetCDF dataset.')
        logger.info('Scientific acquisition completed: files=%d', len(paths))
        registered = self.registry.register(paths)
        if not registered:
            raise DatasetUnavailableError('Acquired Copernicus data failed validation and was not registered.')
        logger.info('Scientific dataset validation succeeded: bundles=%d', len(registered))
        for bundle in registered:
            bundle.metadata['acquisition_product'] = request.product
        resolved = self._matching_bundles(request)
        if not resolved:
            self.registry.unregister(registered)
            raise DatasetUnavailableError('Acquired Copernicus data does not cover the requested subset.')
        self.cache_index.save(self.registry.datasets)
        logger.info('DatasetBundle registered and persistent cache updated: bundles=%d', len(registered))
        if self.on_registered is not None:
            self.on_registered()
            logger.info('Registry and active repository refreshed.')
        return DatasetResolution(tuple(resolved), cache_hit=False)

    def _discover(self) -> None:
        if not self._discovered:
            persisted = self.cache_index.load()
            if persisted:
                self.registry.datasets = persisted
                self.registry.ready = True
                logger.info('Persistent operational cache restored: bundles=%d', len(persisted))
            else:
                self.registry.discover()
            self._discovered = True

    def _matching_bundles(self, request: OperationalDataRequest) -> list[DatasetBundle]:
        matches = []
        for variable in request.variables:
            candidate = next((bundle for bundle in self.registry.by_variable(variable) if self._covers(bundle, request)), None)
            if candidate is None:
                return []
            matches.append(candidate)
        return matches

    @staticmethod
    def _covers(bundle: DatasetBundle, request: OperationalDataRequest) -> bool:
        coverage = bundle.spatial_coverage
        if bundle.provider != request.provider:
            return False
        if bundle.metadata.get('acquisition_product') not in (None, request.product):
            return False
        if request.forecast_cycle and bundle.forecast_cycle != request.forecast_cycle:
            return False
        if request.resolution and bundle.metadata.get('resolution') not in (None, request.resolution):
            return False
        if not (
            coverage.get('min_latitude', float('inf')) <= request.min_latitude
            and coverage.get('max_latitude', float('-inf')) >= request.max_latitude
            and coverage.get('min_longitude', float('inf')) <= request.min_longitude
            and coverage.get('max_longitude', float('-inf')) >= request.max_longitude
        ):
            return False
        return (
            OperationalDataManager._covers_time(bundle, request.start_time, request.end_time)
            and OperationalDataManager._covers_depth(bundle, request.min_depth, request.max_depth)
        )

    @staticmethod
    def _scientific_request(request: OperationalDataRequest) -> ScientificAcquisitionRequest:
        return ScientificAcquisitionRequest(
            provider=request.provider,
            product=request.product,
            variables=request.variables,
            min_latitude=request.min_latitude,
            max_latitude=request.max_latitude,
            min_longitude=request.min_longitude,
            max_longitude=request.max_longitude,
            start_time=request.start_time,
            end_time=request.end_time,
            min_depth=request.min_depth,
            max_depth=request.max_depth,
            resolution=request.resolution,
            forecast_cycle=request.forecast_cycle,
        )

    @staticmethod
    def _covers_time(bundle: DatasetBundle, start: str | None, end: str | None) -> bool:
        if start is None and end is None:
            return True
        coverage = bundle.temporal_coverage
        if not coverage.get('start') or not coverage.get('end'):
            return False
        start_bound = OperationalDataManager._time(coverage['start'])
        end_bound = OperationalDataManager._time(coverage['end'])
        return (start is None or start_bound <= OperationalDataManager._time(start)) and (
            end is None or end_bound >= OperationalDataManager._time(end)
        )

    @staticmethod
    def _covers_depth(bundle: DatasetBundle, minimum: float | None, maximum: float | None) -> bool:
        if minimum is None and maximum is None:
            return True
        depths = bundle.available_depths
        if not depths:
            return False
        return (minimum is None or min(depths) <= minimum) and (maximum is None or max(depths) >= maximum)

    @staticmethod
    def _time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
