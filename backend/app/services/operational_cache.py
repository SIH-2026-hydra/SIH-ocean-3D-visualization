"""Persistent, validated cache index for operational scientific subsets."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.models.dataset_bundle import DatasetBundle


class OperationalCacheIndex:
    """Persist validated request identities and DatasetBundles atomically."""

    FILENAME = '.oceanx-operational-cache.json'

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.path = self.cache_dir / self.FILENAME

    def load(self) -> list[DatasetBundle]:
        if not self.path.is_file():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return []
        bundles = []
        for item in payload.get('bundles', []):
            try:
                bundle = DatasetBundle(
                    **(item | {'source_files': {
                        name: tuple(Path(path) for path in paths)
                        for name, paths in item['source_files'].items()
                    }})
                )
            except (KeyError, TypeError):
                continue
            if all(path.is_file() for paths in bundle.source_files.values() for path in paths):
                bundles.append(bundle)
        return bundles

    def save(self, bundles: list[DatasetBundle]) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {'version': 1, 'bundles': [self._serialize(bundle) for bundle in bundles]}
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(payload, sort_keys=True, separators=(',', ':')), encoding='utf-8')
        temporary.replace(self.path)

    @staticmethod
    def identity(request: Any) -> str:
        """Canonical identity for provider/product and scientific subset dimensions."""
        values = asdict(request)
        return json.dumps(values, sort_keys=True, separators=(',', ':'))

    @staticmethod
    def _serialize(bundle: DatasetBundle) -> dict[str, Any]:
        return {
            'dataset_id': bundle.dataset_id,
            'provider': bundle.provider,
            'product': bundle.product,
            'model': bundle.model,
            'forecast_cycle': bundle.forecast_cycle,
            'variables': list(bundle.variables),
            'coordinate_signature': [list(item) for item in bundle.coordinate_signature],
            'spatial_coverage': bundle.spatial_coverage,
            'temporal_coverage': bundle.temporal_coverage,
            'depth_levels': list(bundle.depth_levels),
            'source_files': {name: [str(path) for path in paths] for name, paths in bundle.source_files.items()},
            'metadata': bundle.metadata,
        }
