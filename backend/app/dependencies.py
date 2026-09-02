from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.repositories import BaseOceanRepository, create_repository


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


def initialize_repository() -> BaseOceanRepository:
    if repository.provider_ready:
        return repository._repository  # type: ignore[return-value]
    instance = create_repository(settings)
    repository.set(instance)
    return instance


def close_repository() -> None:
    if repository.provider_ready:
        repository.close()
        repository.clear()


def get_repository():
    """Return the application-wide configured repository instance."""
    return repository