from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models.dataset_bundle import DatasetBundle
from app.repositories.json_repository import JsonOceanRepository


class NOAAOceanRepository(JsonOceanRepository):
    """Local NOAA-shaped provider used to validate multi-provider integration."""

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir)
        data_path = self.data_dir / 'model_data.json'
        self.dataset_bundles = (
            DatasetBundle(
                dataset_id='noaa-demo-ocean-model',
                provider='NOAA',
                product='NOAA OCEANX DEMO MODEL',
                model='NOAA Regional Ocean Model',
                forecast_cycle='2026-08-24T00:00:00Z',
                variables=('temperature', 'salinity', 'current_u', 'current_v'),
                coordinate_signature=(
                    ('time', 'timestamp'),
                    ('depth', 'depth'),
                    ('latitude', 'latitude'),
                    ('longitude', 'longitude'),
                ),
                spatial_coverage={
                    'min_latitude': 5.0,
                    'max_latitude': 30.0,
                    'min_longitude': 45.0,
                    'max_longitude': 95.0,
                },
                temporal_coverage={
                    'start': '2026-08-24T00:00:00Z',
                    'end': '2026-08-24T20:00:00Z',
                },
                depth_levels=(0.0, 50.0, 100.0, 200.0, 500.0),
                source_files={'model': (data_path,)},
                metadata={
                    'source_type': 'model',
                    'is_synthetic': True,
                    'dataset_name': 'NOAA Demo Ocean Model',
                    'description': 'Local NOAA-compatible demonstration dataset.',
                },
            ),
        )

    def get_provider_capabilities(self) -> dict[str, Any]:
        capabilities = super().get_provider_capabilities()
        capabilities['provider'] = 'NOAA'
        return capabilities

    def get_dataset_metadata(self) -> list[dict[str, Any]]:
        metadata = super().get_dataset_metadata()[0]
        metadata.update({
            'dataset_id': self.dataset_bundles[0].dataset_id,
            'dataset_name': self.dataset_bundles[0].model,
            'source': 'NOAA',
        })
        return [metadata]
