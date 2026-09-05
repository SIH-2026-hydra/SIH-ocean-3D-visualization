from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from app.acquisition.base import ProviderAcquisitionAdapter
from app.acquisition.models import ScientificAcquisitionRequest
from app.repositories.exceptions import ProviderUnavailableError


class AcquisitionManager:
    """Dispatch provider-neutral scientific requests to registered adapters."""

    def __init__(self, adapters: Iterable[ProviderAcquisitionAdapter]) -> None:
        self._adapters = {adapter.provider.lower(): adapter for adapter in adapters}

    @classmethod
    def default(cls) -> 'AcquisitionManager':
        from app.acquisition.copernicus import CopernicusAcquisitionAdapter

        return cls((CopernicusAcquisitionAdapter(),))

    def acquire(self, request: ScientificAcquisitionRequest, destination: Path) -> Sequence[Path]:
        adapter = self._adapters.get(request.provider.lower())
        if adapter is None:
            raise ProviderUnavailableError(f'No acquisition adapter is configured for {request.provider}.')
        return adapter.acquire(request, destination)
