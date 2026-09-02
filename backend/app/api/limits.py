from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from app.core.config import settings


class ResponseLimitExceededError(ValueError):
    """The requested response exceeds a configured API limit."""

    def __init__(self, message: str, *, limit: str) -> None:
        super().__init__(message)
        self.limit = limit


def enforce_response_limits(payload: Mapping[str, Any]) -> None:
    records = payload.get('data')
    if isinstance(records, Sequence) and not isinstance(records, (str, bytes, bytearray)):
        if len(records) > settings.max_response_cells:
            raise ResponseLimitExceededError(
                f'Response contains {len(records)} cells; maximum is {settings.max_response_cells}.',
                limit='max_response_cells',
            )
        dimensions = _grid_dimensions(records)
        oversized = {name: size for name, size in dimensions.items() if size > settings.max_grid_dimension}
        if oversized:
            raise ResponseLimitExceededError(
                f'Response grid dimensions exceed the maximum of {settings.max_grid_dimension}: {oversized}.',
                limit='max_grid_dimension',
            )
    encoded_size = len(json.dumps(payload, default=str, separators=(',', ':')).encode('utf-8'))
    if encoded_size > settings.max_response_size_bytes:
        raise ResponseLimitExceededError(
            f'Response size is {encoded_size} bytes; maximum is {settings.max_response_size_bytes}.',
            limit='max_response_size_bytes',
        )


def _grid_dimensions(records: Sequence[Any]) -> dict[str, int]:
    dimensions: dict[str, set[Any]] = {name: set() for name in ('latitude', 'longitude', 'depth', 'timestamp')}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        for name in dimensions:
            if name in record:
                dimensions[name].add(str(record[name]))
    return {name: len(values) for name, values in dimensions.items() if values}