"""Copernicus Marine SDK adapter, isolated from backend business services."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Sequence

from app.acquisition.models import ScientificAcquisitionRequest
from app.repositories.exceptions import ProviderUnavailableError


class CopernicusAcquisitionAdapter:
    provider = 'Copernicus Marine'
    DATASET_ID = 'GLOBAL_ANALYSISFORECAST_PHY_001_024'
    SOURCE_VARIABLES = {
        'temperature': 'thetao', 'salinity': 'so', 'current_u': 'uo', 'current_v': 'vo',
    }

    def acquire(self, request: ScientificAcquisitionRequest, destination: Path) -> Sequence[Path]:
        try:
            import copernicusmarine
        except ImportError as exc:
            raise ProviderUnavailableError(
                'Copernicus acquisition is unavailable: install the provider runtime package.'
            ) from exc

        try:
            variables = [self.SOURCE_VARIABLES[item] for item in request.variables]
        except KeyError as exc:
            raise ValueError(f'Copernicus does not support requested variable: {exc.args[0]}') from exc
        if request.product != 'physical-forecast':
            raise ValueError(f'Copernicus does not support scientific product: {request.product}')
        destination.mkdir(parents=True, exist_ok=True)
        fingerprint = sha256(repr(request).encode('utf-8')).hexdigest()[:16]
        output_name = f'copernicus_{fingerprint}.nc'
        result = copernicusmarine.subset(
            dataset_id=self.DATASET_ID,
            variables=variables,
            minimum_latitude=request.min_latitude,
            maximum_latitude=request.max_latitude,
            minimum_longitude=request.min_longitude,
            maximum_longitude=request.max_longitude,
            start_datetime=request.start_time,
            end_datetime=request.end_time,
            minimum_depth=request.min_depth,
            maximum_depth=request.max_depth,
            output_directory=str(destination),
            output_filename=output_name,
            force_download=True,
        )
        if isinstance(result, (str, Path)):
            return (Path(result),)
        output = destination / output_name
        return (output,) if output.is_file() else tuple(destination.glob(f'copernicus_{fingerprint}*.nc'))
