# Project Context

## Project
SIH26067 - Web-Based Interactive 3D Visualization of Numerical Ocean Models and In-Situ Observations

## Prototype
Prototype 1 with backend foundation and frontend infrastructure.

## Current phase
Backend Phase 2 (Ocean Data Engine Complete) + Frontend Infrastructure Phase 1 (Complete)

## Architecture
- Frontend: React 18 + Vite 5 + CesiumJS 1.120 (global 3D Earth visualization)
- Backend: FastAPI with FastAPI + Pydantic v2 (API layer)
- Service layer: OceanDataService (orchestration and generic spatial/depth/time filtering)
- Repository layer: JsonOceanRepository (data abstraction)
- Data source: deterministic synthetic JSON dataset with global-capable normalized ocean-state schema
- Data flow: Data Source → Repository/Provider → Normalization → OceanDataService → FastAPI → future Cesium frontend

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

Phase 2 adds a generic ocean-state data layer that treats ocean state as f(latitude, longitude, depth, time) and keeps bathymetry conceptually separate from 4D ocean variables.

## Current endpoints
- /api/v1/health
- /api/v1/model
- /api/v1/observations
- /api/v1/metadata
- /api/v1/ocean
- /api/v1/ocean/point

## Current data source
Deterministic synthetic JSON data stored under backend/app/data/ for a lightweight but visualization-ready Indian Ocean demo grid. Data remains globally capable and is deliberately labelled as synthetic.

## Synthetic-data status
All demo records are clearly marked as synthetic and intended for validation only. No observation or ML prediction values are fabricated for this phase.

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

## Phase 2 milestone
Ocean Data Engine is in place with global-capable normalized fields for temperature, salinity, current vectors, temporal filtering, and point queries. The Phase 1 frontend remains untouched, and future visualization work will consume the generic /api/v1/ocean and /api/v1/ocean/point API contracts.

## Phase 4 milestone
Point inspection is added for user-driven click queries against the existing /api/v1/ocean/point endpoint. The selection flow uses the current time/depth state, resolves clicked globe coordinates with Cesium, updates a single selected-location marker, and renders a glass inspector panel without changing the underlying backend contract or the existing viewer architecture.

## Phase 5 milestone
Depth exploration uses one shared selectedDepth state, initialized to Surface / 0 m and sourced from metadata when available. The depth control refreshes the temperature field and selected point with the shared timestamp, while aborting stale requests and preserving the selected marker location.

## Phase 6 milestone
Time exploration uses one shared selectedTime ISO timestamp, initialized from the earliest metadata timestep. A discrete UTC timeline controls temperature data and the selected point together, with previous/next navigation, stopped-at-end playback, and abortable requests for rapid changes.

## Phase 7 milestone
Parameter exploration uses one shared selectedParameter state for temperature, salinity, and current while preserving selectedDepth, selectedTime, selectedLocation, and camera state. Temperature and salinity use the reusable scalar field renderer; current uses a capped static vector layer with speed-derived arrow length and no animation.

Phase 6 temporal navigation now separates metadata-derived UTC date selection from selected-date time-of-day selection while retaining selectedTime as the only canonical value. Date navigation remains compact for future multi-year metadata, and scientific field requests stay lazy for the selected depth/time only.

## Next milestone
Phase 7 will be reserved for the next extension after time exploration and its verification are complete.
