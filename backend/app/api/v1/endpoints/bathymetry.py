"""API endpoints for bathymetry/seafloor depth queries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import get_repository
from app.services.bathymetry_service import BathymetryService

router = APIRouter()
repository = get_repository()
service = BathymetryService(repository)


def _parse_optional_float(value: str | None, *, name: str) -> float | None:
    """Parse optional float query parameter."""
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
    """Validate latitude/longitude bounds."""
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


@router.get('/bathymetry')
def get_bathymetry(
    min_lat: str | None = Query(default=None, description='Minimum latitude'),
    max_lat: str | None = Query(default=None, description='Maximum latitude'),
    min_lon: str | None = Query(default=None, description='Minimum longitude'),
    max_lon: str | None = Query(default=None, description='Maximum longitude'),
) -> dict[str, object]:
    """
    Query bathymetry data within geographic bounds.
    
    Returns array of bathymetry records with static geographic depth information.
    """
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

    records = service.get_bathymetry_records()
    filtered = service.filter_records(
        records,
        min_lat=parsed_min_lat,
        max_lat=parsed_max_lat,
        min_lon=parsed_min_lon,
        max_lon=parsed_max_lon,
    )

    return {
        'data': filtered,
        'count': len(filtered),
        'total': len(records),
    }


@router.get('/bathymetry/point')
def get_bathymetry_point(
    lat: str = Query(..., description='Latitude'),
    lon: str = Query(..., description='Longitude'),
) -> dict[str, object]:
    """
    Query bathymetry at a specific geographic point.
    
    Returns the nearest bathymetry record with seafloor depth, water column,
    matched location, source information, and synthetic flag.
    """
    parsed_lat = _parse_optional_float(lat, name='lat')
    parsed_lon = _parse_optional_float(lon, name='lon')

    if parsed_lat is None or parsed_lon is None:
        raise HTTPException(status_code=400, detail='lat and lon are required.')
    if not -90.0 <= parsed_lat <= 90.0:
        raise HTTPException(status_code=400, detail='Latitude must be between -90 and 90 degrees.')
    if not -180.0 <= parsed_lon <= 180.0:
        raise HTTPException(status_code=400, detail='Longitude must be between -180 and 180 degrees.')

    result = service.get_point_bathymetry(parsed_lat, parsed_lon)

    if result is None:
        raise HTTPException(status_code=404, detail='No bathymetry data available at this location.')

    return result
