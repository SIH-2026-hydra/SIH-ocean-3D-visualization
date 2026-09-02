from fastapi import APIRouter

from app.api.limits import enforce_response_limits
from app.dependencies import get_repository
from app.models.discovery import (
    CapabilityResponse,
    CatalogResponse,
    CoverageResponse,
    VariableResponse,
)
from app.services.discovery_service import DiscoveryService

router = APIRouter()
service = DiscoveryService(get_repository())


@router.get('/datasets', response_model=CatalogResponse)
def get_dataset_catalog() -> CatalogResponse:
    payload = {'datasets': service.catalog()}
    enforce_response_limits(payload)
    return CatalogResponse.model_validate(payload)


@router.get('/variables', response_model=VariableResponse)
def get_variable_discovery() -> VariableResponse:
    return VariableResponse(variables=service.variables())


@router.get('/coverage', response_model=CoverageResponse)
def get_coverage_discovery() -> CoverageResponse:
    return CoverageResponse(coverage=service.coverage())


@router.get('/capabilities', response_model=CapabilityResponse)
def get_capability_discovery() -> CapabilityResponse:
    return CapabilityResponse(capabilities=service.capabilities())
