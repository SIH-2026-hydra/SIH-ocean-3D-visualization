# Project Context

## Project
SIH26067 - Web-Based Interactive 3D Visualization of Numerical Ocean Models and In-Situ Observations

## Prototype
Prototype 1 with backend foundation and frontend infrastructure.

## Current phase
Backend Phase 1 (Complete) + Frontend Infrastructure Phase 1 (Complete)

## Architecture
- Frontend: React 18 + Vite 5 + CesiumJS 1.120 (global 3D Earth visualization)
- Backend: FastAPI with FastAPI + Pydantic v2 (API layer)
- Service layer: OceanDataService (orchestration)
- Repository layer: JsonOceanRepository (data abstraction)
- Data source: small synthetic JSON dataset

The frontend renders a global interactive 3D Earth using CesiumJS. The Indian Ocean is the default Prototype 1 demonstration viewport, not a geographic restriction. Future data loading will use regional bounding-box requests to fetch only the visible geographic subset.

## Frontend stack
- Node.js 18+
- React 18
- Vite 5
- CesiumJS 1.120
- ESLint 9

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

### Backend (Phase 1 - Complete)
- Windows-local virtual environment setup
- FastAPI application shell
- Centralized configuration
- Pydantic schemas for model, observation, and dataset metadata
- JSON repository and service layer
- Demo Arabian Sea data (synthetic, clearly labeled)
- API endpoints for health, model, observations, and metadata
- pytest coverage (7 passing tests)
- Backend documentation and new team member checklist

### Frontend Infrastructure (Phase 1 - Complete)
- Windows-compatible Vite + React project structure
- CesiumJS npm installation and asset configuration
- Environment variable handling (.env.example, safe .gitignore)
- ESLint configuration for React and Vite
- Comprehensive frontend README with setup instructions
- Global geographic architecture (Earth-based, not Indian-Ocean-limited)
- Reserved component structure for separate frontend AI implementation
- No fake UI or demo code; infrastructure only

## Known limitations
- No real ocean APIs or external data integrations yet
- No NetCDF/xarray processing yet
- No database layer or advanced analytics yet
- Cesium globe rendering not yet implemented (reserved for next phase)
- Frontend React components not yet written (reserved for separate frontend AI)
- No ocean data visualization on the globe yet
- No backend integration with frontend yet

## Geographic Architecture

This is a **global** platform:
- Cesium renders the full Earth
- Indian Ocean is the default Prototype 1 demonstration viewport
- Users can navigate globally
- Future data loading will use bounding-box filtering for regional subsets
- ML/data pipelines may operate on global ocean datasets

## Next milestone
Frontend AI tool will implement the Phase 1 global Cesium globe with initial Indian Ocean camera position, rotation/zoom/pan navigation, and Home/Reset functionality. Backend API integration and ocean data visualization will follow after globe validation.
