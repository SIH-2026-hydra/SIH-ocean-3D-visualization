from fastapi import APIRouter, HTTPException, Query

from app.dependencies import get_repository
from app.services.ocean_data_service import OceanDataService
from app.models.schemas import ModelResponse
from app.api.limits import enforce_response_limits

router = APIRouter()
repository = get_repository()
service = OceanDataService(repository)


@router.get('/model', response_model=ModelResponse)
def get_model_records(
    depth: str | None = Query(default=None, description='Optional depth filter in meters'),
) -> ModelResponse:
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
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail='Configured ocean provider is unavailable.') from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=404, detail='No model records found for the requested depth.')
    dataset_metadata = service.get_dataset_metadata()
    dataset = dataset_metadata[0] if dataset_metadata else {}
    payload = {
        'metadata': {
            'count': len(records),
            'sourceType': dataset.get('source_type', 'model'),
            'isSynthetic': bool(dataset.get('is_synthetic', True)),
        },
        'data': records,
    }
    enforce_response_limits(payload)
    return ModelResponse.model_validate(payload)
