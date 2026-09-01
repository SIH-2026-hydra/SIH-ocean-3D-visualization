"""API endpoints for in-situ observation measurements."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.repositories.json_repository import JsonOceanRepository
from app.services.observation_service import ObservationService

router = APIRouter()
service = ObservationService(JsonOceanRepository())


def parse_float(value: str | None, name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f'{name} must be numeric.') from exc


def parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return service.normalize_timestamp(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='time must be a valid ISO-8601 UTC timestamp.') from exc


def validate_bounds(min_lat: float | None, max_lat: float | None, min_lon: float | None, max_lon: float | None) -> None:
    for name, value, lower, upper in (
        ('min_lat', min_lat, -90.0, 90.0), ('max_lat', max_lat, -90.0, 90.0),
        ('min_lon', min_lon, -180.0, 180.0), ('max_lon', max_lon, -180.0, 180.0),
    ):
        if value is not None and not lower <= value <= upper:
            raise HTTPException(status_code=400, detail=f'{name} must be between {lower} and {upper}.')
    if min_lat is not None and max_lat is not None and min_lat > max_lat:
        raise HTTPException(status_code=400, detail='min_lat cannot be greater than max_lat.')
    if min_lon is not None and max_lon is not None and min_lon > max_lon:
        raise HTTPException(status_code=400, detail='min_lon cannot be greater than max_lon.')


@router.get('/observations')
def get_observations(depth: str | None = None, time: str | None = None, min_lat: str | None = None, max_lat: str | None = None, min_lon: str | None = None, max_lon: str | None = None, parameter: str | None = Query(default=None), platform_type: str | None = None) -> dict[str, object]:
    parsed_depth = parse_float(depth, 'depth')
    if parsed_depth is not None and parsed_depth < 0:
        raise HTTPException(status_code=400, detail='depth must be greater than or equal to 0.')
    bounds = [parse_float(value, name) for value, name in ((min_lat, 'min_lat'), (max_lat, 'max_lat'), (min_lon, 'min_lon'), (max_lon, 'max_lon'))]
    validate_bounds(*bounds)
    try:
        records = service.get_records(depth=parsed_depth, timestamp=parse_timestamp(time), min_lat=bounds[0], max_lat=bounds[1], max_lon=bounds[3], min_lon=bounds[2], parameter=parameter, platform_type=platform_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'metadata': {'count': len(records), 'sourceType': 'observation', 'isSynthetic': True}, 'data': records}


@router.get('/observations/nearest')
def get_nearest_observation(lat: float = Query(..., ge=-90.0, le=90.0), lon: float = Query(..., ge=-180.0, le=180.0), depth: float = Query(..., ge=0.0), time: str = Query(...)) -> dict[str, object]:
    timestamp = parse_timestamp(time)
    observation = service.find_nearest(latitude=lat, longitude=lon, depth=depth, timestamp=timestamp)
    return {'available': observation is not None, 'requested_location': {'latitude': lat, 'longitude': lon}, 'requested_depth': depth, 'requested_time': time, 'observation': observation}
