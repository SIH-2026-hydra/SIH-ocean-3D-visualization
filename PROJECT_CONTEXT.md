# Project Context

## Project
SIH26067 - Web-Based Interactive 3D Visualization of Numerical Ocean Models and In-Situ Observations

## Prototype
Prototype 1 backend foundation for demo data and API validation.

## Current phase
Backend Phase 1

## Architecture
- API layer: FastAPI
- Service layer: OceanDataService
- Repository layer: JsonOceanRepository
- Data source: small synthetic JSON dataset

## Backend stack
- Python 3.11+
- FastAPI
- Pydantic v2
- pytest
- Uvicorn

## Data architecture
The backend normalizes model and observation records into a consistent schema before exposing them through the API. This keeps future storage backends replaceable without redesigning the frontend contract.

## Current endpoints
- /api/v1/health
- /api/v1/model
- /api/v1/observations
- /api/v1/metadata

## Current data source
Synthetic JSON files stored under backend/app/data/

## Synthetic-data status
All demo records are clearly marked as synthetic and intended for validation only.

## Completed work
- Windows-local virtual environment setup
- FastAPI application shell
- Centralized configuration
- Pydantic schemas for model, observation, and dataset metadata
- JSON repository and service layer
- Demo Arabian Sea data
- API endpoints for health, model, observation, and metadata
- Initial pytest coverage for the backend

## Known limitations
- No real ocean APIs or external data integrations yet
- No NetCDF/xarray processing yet
- No database layer or advanced analytics yet
- No frontend or 3D visualization yet

## Next milestone
Add richer scientific filters and deeper metadata while keeping the same normalized architecture for future backend storage replacements.
