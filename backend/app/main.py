from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.dependencies import close_repository, initialize_repository, repository
from app.api.limits import ResponseLimitExceededError
from app.models.schemas import ApiError, ApiErrorResponse
from app.repositories.exceptions import (
    DataUnavailableError,
    DatasetUnavailableError,
    InvalidProviderQueryError,
    ProviderError,
    ProviderUnavailableError,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        initialize_repository()
        yield
    finally:
        close_repository()

app = FastAPI(
    title=settings.app_name,
    version='0.1.0',
    description='Backend API for SIH26067 Prototype 1',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        'http://localhost:3000',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:3000',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


def _error_response(status_code: int, code: str, message: str, details: dict[str, object] | None = None) -> JSONResponse:
    payload = ApiErrorResponse(
        detail=message,
        error=ApiError(code=code, message=message, details=details or {}),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@app.exception_handler(ResponseLimitExceededError)
async def response_limit_handler(_: Request, exc: ResponseLimitExceededError) -> JSONResponse:
    return _error_response(413, 'response_limit_exceeded', str(exc), {'limit': exc.limit})


@app.exception_handler(ProviderError)
async def provider_error_handler(_: Request, exc: ProviderError) -> JSONResponse:
    if isinstance(exc, (DatasetUnavailableError, ProviderUnavailableError)):
        status_code, code = 503, 'provider_unavailable'
    elif isinstance(exc, DataUnavailableError):
        status_code, code = 404, 'data_unavailable'
    elif isinstance(exc, InvalidProviderQueryError):
        status_code, code = 400, 'invalid_provider_query'
    else:
        status_code, code = 500, 'provider_error'
    return _error_response(status_code, code, str(exc))


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = str(exc.detail)
    return _error_response(exc.status_code, 'http_error', message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(422, 'validation_error', 'Request validation failed.', {'errors': exc.errors()})


@app.get('/')
def root() -> dict[str, str]:
    return {'service': settings.app_name, 'status': 'ok'}
