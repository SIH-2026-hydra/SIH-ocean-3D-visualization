from fastapi import APIRouter, HTTPException

from app.dependencies import get_repository
from app.services.ocean_data_service import OceanDataService

router = APIRouter()
repository = get_repository()
service = OceanDataService(repository)


@router.get('/metadata')
def get_metadata() -> dict[str, object]:
    try:
        records = service.get_dataset_metadata()
        discovery = service.get_ocean_discovery()
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail='Configured ocean provider is unavailable.') from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=404, detail='No dataset metadata available.')

    return {
        'metadata': {
            'count': len(records),
            'sourceType': 'dataset',
            'isSynthetic': bool(records[0].get('is_synthetic', True)) if records else True,
        },
        'discovery': discovery,
        'data': records,
    }
