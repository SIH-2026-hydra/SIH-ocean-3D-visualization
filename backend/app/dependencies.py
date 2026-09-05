from __future__ import annotations

from typing import Any
import logging

from app.core.config import settings
from app.repositories import BaseOceanRepository, create_repository
from app.services.operational_data_manager import OperationalDataManager

logger = logging.getLogger(__name__)


class DeferredRepository:
    """Resolve the application provider only after FastAPI startup."""

    def __init__(self) -> None:
        self._repository: BaseOceanRepository | None = None

    def set(self, repository: BaseOceanRepository) -> None:
        self._repository = repository

    def clear(self) -> None:
        self._repository = None

    def __getattr__(self, name: str) -> Any:
        if self._repository is None:
            if request_driven_activation_enabled():
                from app.repositories.exceptions import DatasetUnavailableError

                raise DatasetUnavailableError('No scientific provider is active; waiting for a request-driven acquisition.')
            initialize_repository()
        return getattr(self._repository, name)

    @property
    def provider_ready(self) -> bool:
        return self._repository is not None

    @property
    def registry_ready(self) -> bool:
        if self._repository is None:
            return False
        registry = getattr(self._repository, 'registry', None)
        return True if registry is None else registry.ready


repository = DeferredRepository()
operational_data_manager: OperationalDataManager | None = None


def request_driven_activation_enabled() -> bool:
    """Whether ``auto`` deliberately leaves the provider unbound at startup."""
    return settings.ocean_provider.lower().strip() == 'auto' and settings.copernicus_acquisition_enabled


def initialize_repository() -> BaseOceanRepository | None:
    if request_driven_activation_enabled() and not repository.provider_ready:
        logger.info('Application ready; waiting for scientific requests before provider activation.')
        return None
    if repository.provider_ready:
        return repository._repository  # type: ignore[return-value]
    instance = create_repository(settings)
    repository.set(instance)
    return instance


def close_repository() -> None:
    if repository.provider_ready:
        repository.close()
        repository.clear()


def get_operational_data_manager() -> OperationalDataManager | None:
    """Create the opt-in acquisition manager only for Copernicus sessions."""
    global operational_data_manager
    if not settings.copernicus_acquisition_enabled or settings.ocean_provider.lower() not in {'auto', 'copernicus'}:
        return None
    if operational_data_manager is None:
        cache_dir = settings.copernicus_cache_dir
        operational_data_manager = OperationalDataManager(
            cache_dir,
            on_registered=_refresh_repository,
            on_available=_activate_repository,
        )
    return operational_data_manager


def _refresh_repository() -> None:
    close_repository()
    # The request has already acquired and registered a valid bundle, so bind
    # the normal repository without reintroducing startup-time activation.
    instance = create_repository(settings)
    repository.set(instance)


def _activate_repository() -> None:
    """Bind restored operational data only when no request provider is active."""
    if repository.provider_ready:
        return
    # This is called only after OperationalDataManager has resolved a valid
    # cached bundle, preserving the no-provider startup lifecycle.
    instance = create_repository(settings)
    repository.set(instance)


def get_repository():
    """Return the application-wide configured repository instance."""
    return repository
