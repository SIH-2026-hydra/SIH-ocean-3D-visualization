from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version='0.1.0',
    description='Backend API for SIH26067 Prototype 1',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, 'http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get('/')
def root() -> dict[str, str]:
    return {'service': settings.app_name, 'status': 'ok'}
