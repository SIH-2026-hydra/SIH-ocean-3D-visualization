from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from app.acquisition.models import ScientificAcquisitionRequest


class ProviderAcquisitionAdapter(Protocol):
    """Adapter boundary for provider SDKs, APIs, and credentials."""

    provider: str

    def acquire(self, request: ScientificAcquisitionRequest, destination: Path) -> Sequence[Path]: ...
