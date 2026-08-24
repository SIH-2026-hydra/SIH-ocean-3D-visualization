from fastapi import APIRouter

router = APIRouter()


@router.get('/health')
def health() -> dict[str, str]:
    return {
        'status': 'ok',
        'service': 'ocean-intelligence-api',
        'version': '0.1.0',
    }
