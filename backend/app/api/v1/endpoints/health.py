from fastapi import APIRouter

from app.dependencies import repository

router = APIRouter()


@router.get('/health')
def health() -> dict[str, object]:
    return {
        'status': 'ok',
        'service': 'ocean-intelligence-api',
        'version': '0.1.0',
        'provider_ready': repository.provider_ready,
        'registry_ready': repository.registry_ready,
    }
