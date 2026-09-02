"""API endpoints for ML point predictions."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import get_repository
from app.services.prediction_service import PredictionService
from app.models.schemas import PredictionResponse
from app.api.limits import enforce_response_limits

router = APIRouter()
service = PredictionService(get_repository())


def parse_float(value: str | None, name: str) -> float | None:
    """Parse optional float value."""
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f'{name} must be numeric.') from exc


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse optional ISO-8601 timestamp."""
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail='time must be a valid ISO-8601 UTC timestamp.'
        ) from exc


@router.get('/predictions/point', response_model=PredictionResponse)
def get_point_prediction(
    lat: float = Query(..., ge=-90.0, le=90.0, description='Latitude in decimal degrees'),
    lon: float = Query(..., ge=-180.0, le=180.0, description='Longitude in decimal degrees'),
    depth: str = Query(..., description='Depth in meters'),
    time: str = Query(..., description='UTC timestamp (ISO-8601)'),
) -> PredictionResponse:
    """Get ML point prediction for ocean state at specified location.
    
    Parameters:
    - lat: Latitude (-90 to 90)
    - lon: Longitude (-180 to 180)
    - depth: Depth in meters (≥ 0)
    - time: ISO-8601 UTC timestamp
    
    Returns: Point prediction with temperature, salinity, currents, and model metadata.
    
    Returns null/unavailable if point is below local seafloor or unsupported.
    """
    parsed_depth = parse_float(depth, 'depth')
    if parsed_depth is None or parsed_depth < 0:
        raise HTTPException(status_code=400, detail='depth must be numeric and ≥ 0.')

    parsed_time = parse_timestamp(time)
    if not parsed_time:
        raise HTTPException(status_code=400, detail='time is required and must be valid ISO-8601.')

    prediction, unavailable_reason = service.predict_point(
        latitude=lat,
        longitude=lon,
        depth=parsed_depth,
        timestamp=parsed_time,
    )

    payload = {
        'requested_location': {'latitude': lat, 'longitude': lon},
        'requested_depth': parsed_depth,
        'requested_time': time,
        'available': prediction is not None,
        'unavailable_reason': unavailable_reason,
        'prediction': prediction,
    }
    enforce_response_limits(payload)
    return PredictionResponse.model_validate(payload)
