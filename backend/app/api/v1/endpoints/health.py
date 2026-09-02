from fastapi import APIRouter

from app.dependencies import repository
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get('/health', response_model=HealthResponse)
def health() -> HealthResponse:
    return {
        'status': 'ok',
        'service': 'ocean-intelligence-api',
        'version': '0.1.0',
        'provider_ready': repository.provider_ready,
        'registry_ready': repository.registry_ready,
    }
