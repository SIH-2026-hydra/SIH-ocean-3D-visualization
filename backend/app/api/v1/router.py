from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.metadata import router as metadata_router
from app.api.v1.endpoints.model import router as model_router
from app.api.v1.endpoints.ocean import router as ocean_router
from app.api.v1.endpoints.observations import router as observations_router

router = APIRouter()

router.include_router(health_router)
router.include_router(metadata_router)
router.include_router(model_router)
router.include_router(ocean_router)
router.include_router(observations_router)
