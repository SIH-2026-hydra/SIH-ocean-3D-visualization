from fastapi import APIRouter, HTTPException

from app.repositories.json_repository import JsonOceanRepository
from app.services.ocean_data_service import OceanDataService

router = APIRouter()
repository = JsonOceanRepository()
service = OceanDataService(repository)


@router.get('/metadata')
def get_metadata() -> dict[str, object]:
    try:
        records = service.get_dataset_metadata()
        discovery = service.get_ocean_discovery()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=404, detail='No dataset metadata available.')

    return {
        'metadata': {
            'count': len(records),
            'sourceType': 'dataset',
            'isSynthetic': True,
        },
        'discovery': discovery,
        'data': records,
    }
