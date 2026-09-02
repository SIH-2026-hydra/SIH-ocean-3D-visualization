from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.dependencies import close_repository, initialize_repository, repository


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


@app.get('/')
def root() -> dict[str, str]:
    return {'service': settings.app_name, 'status': 'ok'}
