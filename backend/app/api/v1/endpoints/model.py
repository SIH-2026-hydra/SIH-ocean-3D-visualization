from fastapi import APIRouter, HTTPException, Query

from app.repositories.json_repository import JsonOceanRepository
from app.services.ocean_data_service import OceanDataService

router = APIRouter()
repository = JsonOceanRepository()
service = OceanDataService(repository)


@router.get('/model')
def get_model_records(
    depth: str | None = Query(default=None, description='Optional depth filter in meters'),
) -> dict[str, object]:
    parsed_depth: float | None = None
    if depth is not None:
        try:
            parsed_depth = float(depth)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail='Depth must be a numeric value in meters.') from exc
        if parsed_depth < 0:
            raise HTTPException(status_code=400, detail='Depth must be greater than or equal to 0.')

    try:
        records = service.get_model_records(depth=parsed_depth)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=404, detail='No model records found for the requested depth.')

    return {
        'metadata': {
            'count': len(records),
            'sourceType': 'model',
            'isSynthetic': True,
        },
        'data': records,
    }
