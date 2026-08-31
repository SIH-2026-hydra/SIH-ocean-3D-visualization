from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query

from app.repositories.json_repository import JsonOceanRepository
from app.services.ocean_data_service import OceanDataService

router = APIRouter()
repository = JsonOceanRepository()
service = OceanDataService(repository)


def _parse_optional_float(value: str | None, *, name: str) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f'{name} must be numeric.') from exc
    return parsed


def _validate_lat_lon_bounds(
    *,
    min_lat: float | None,
    max_lat: float | None,
    min_lon: float | None,
    max_lon: float | None,
) -> None:
    bounds = [
        ('min_lat', min_lat, -90.0, 90.0),
        ('max_lat', max_lat, -90.0, 90.0),
        ('min_lon', min_lon, -180.0, 180.0),
        ('max_lon', max_lon, -180.0, 180.0),
    ]
    for name, value, lower, upper in bounds:
        if value is None:
            continue
        if not lower <= value <= upper:
            raise HTTPException(status_code=400, detail=f'{name} must be between {lower} and {upper}.')
    if min_lat is not None and max_lat is not None and min_lat > max_lat:
        raise HTTPException(status_code=400, detail='min_lat cannot be greater than max_lat.')
    if min_lon is not None and max_lon is not None and min_lon > max_lon:
        raise HTTPException(status_code=400, detail='min_lon cannot be greater than max_lon.')


@router.get('/ocean')
def get_ocean(
    parameter: str = Query(default='temperature', description='Ocean variable to return: temperature, salinity, current'),
    depth: str | None = Query(default=None, description='Optional depth in meters'),
    time: str | None = Query(default=None, description='Optional UTC timestamp (ISO-8601)'),
    min_lat: str | None = Query(default=None, description='Minimum latitude'),
    max_lat: str | None = Query(default=None, description='Maximum latitude'),
    min_lon: str | None = Query(default=None, description='Minimum longitude'),
    max_lon: str | None = Query(default=None, description='Maximum longitude'),
    lat: str | None = Query(default=None, description='Optional latitude validation alias'),
    lon: str | None = Query(default=None, description='Optional longitude validation alias'),
    source: str | None = Query(default=None, description='Optional source filter'),
) -> dict[str, object]:
    if parameter not in service.VALID_PARAMETERS:
        raise HTTPException(status_code=400, detail=f'Unsupported parameter: {parameter}. Valid options: {sorted(service.VALID_PARAMETERS)}')

    parsed_lat = _parse_optional_float(lat, name='lat')
    parsed_lon = _parse_optional_float(lon, name='lon')
    if parsed_lat is not None and not -90.0 <= parsed_lat <= 90.0:
        raise HTTPException(status_code=400, detail='Latitude must be between -90 and 90 degrees.')
    if parsed_lon is not None and not -180.0 <= parsed_lon <= 180.0:
        raise HTTPException(status_code=400, detail='Longitude must be between -180 and 180 degrees.')

    parsed_depth = _parse_optional_float(depth, name='depth')
    if parsed_depth is not None and parsed_depth < 0:
        raise HTTPException(status_code=400, detail='Depth must be greater than or equal to 0.')

    parsed_min_lat = _parse_optional_float(min_lat, name='min_lat')
    parsed_max_lat = _parse_optional_float(max_lat, name='max_lat')
    parsed_min_lon = _parse_optional_float(min_lon, name='min_lon')
    parsed_max_lon = _parse_optional_float(max_lon, name='max_lon')
    _validate_lat_lon_bounds(
        min_lat=parsed_min_lat,
        max_lat=parsed_max_lat,
        min_lon=parsed_min_lon,
        max_lon=parsed_max_lon,
    )

    if time is not None:
        try:
            service._normalize_timestamp(time)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail='time must be a valid ISO-8601 UTC timestamp.') from exc

    try:
        records = service.get_ocean_records(
            parameter=parameter,
            depth=parsed_depth,
            timestamp=time,
            min_lat=parsed_min_lat,
            max_lat=parsed_max_lat,
            min_lon=parsed_min_lon,
            max_lon=parsed_max_lon,
            source=source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    unit_map = {
        'temperature': '°C',
        'salinity': 'PSU',
        'current': 'm/s',
    }

    return {
        'query': {
            'parameter': parameter,
            'depth': parsed_depth,
            'timestamp': time,
            'min_lat': parsed_min_lat,
            'max_lat': parsed_max_lat,
            'min_lon': parsed_min_lon,
            'max_lon': parsed_max_lon,
            'source': source,
        },
        'metadata': {
            'unit': unit_map[parameter],
            'sourceType': 'model',
            'isSynthetic': True,
            'count': len(records),
        },
        'data': records,
    }


@router.get('/ocean/point')
def get_ocean_point(
    lat: float = Query(..., ge=-90.0, le=90.0, description='Latitude in decimal degrees'),
    lon: float = Query(..., ge=-180.0, le=180.0, description='Longitude in decimal degrees'),
    depth: float = Query(..., ge=0.0, description='Depth in meters'),
    time: str = Query(..., description='UTC timestamp for nearest matching grid cell'),
) -> dict[str, object]:
    try:
        service._normalize_timestamp(time)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='time must be a valid ISO-8601 UTC timestamp.') from exc

    try:
        point = service.get_ocean_point(latitude=lat, longitude=lon, depth=depth, timestamp=time)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return point
