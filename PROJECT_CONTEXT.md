# Project Context

## Project
SIH26067 - Web-Based Interactive 3D Visualization of Numerical Ocean Models and In-Situ Observations

## Prototype
Prototype 1 with backend foundation and frontend infrastructure.

## Current phase
Prototype 2.1 Phase 3: local Copernicus dataset discovery, validation, registry, and multi-dataset selection. JSON remains the default provider.

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
- /api/v1/predictions/point

## Current data source
Deterministic synthetic JSON data stored under backend/app/data/ for a lightweight but visualization-ready Indian Ocean demo grid. Data remains globally capable and is deliberately labelled as synthetic.

## Synthetic-data status
All demo records are clearly marked as synthetic and intended for validation only. ML point predictions are deterministic experimental prototype output, not operational forecasts.

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
- Copernicus NetCDF files can be discovered and validated from a configured local directory; downloading and caching are not implemented
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

## Prototype 2.2 Phase 4 milestone
- Added DatasetBundle-backed discovery APIs at `/api/v1/datasets`, `/api/v1/variables`, `/api/v1/coverage`, and `/api/v1/capabilities`.
- DiscoveryService translates the repository's retained DatasetBundle objects into public catalog, variable, coverage, and capability responses without inspecting files or exposing paths.
- Derived products are included in variable and capability discovery with their source variables and units; existing data APIs remain unchanged.

## Phase 9A / 9B milestone
- A replaceable deterministic `PrototypePredictor` supplies experimental/synthetic point predictions independently of model state and observations.
- The inspector compares model and prediction values to a valid nearby observation only, per variable and at one selected point.
- Signed differences and absolute errors are point-wise diagnostics, not aggregate accuracy metrics; no MAE/RMSE or superiority claim is made.

## Prototype 2.1 Phase 1 milestone
- Added an unregistered `CopernicusNetCDFRepository` for locally staged Copernicus NetCDF files.
- Normalizes `thetao`, `so`, `uo`, and `vo` to OCEANX model fields and derives current speed.
- Supports offline coordinate bounds, nearest time/depth selection, requested versus matched depth, missing-value preservation, and real-data provenance.
- The active JSON repository, FastAPI endpoints, frontend, synthetic observations, and prototype ML comparison remain unchanged.

## Prototype 2.1 Phase 2 milestone
- `OCEAN_PROVIDER=json|copernicus` selects the repository through centralized application dependencies.
- `OceanDataService` delegates nearest real-data coordinate/time/depth selection to the Copernicus provider while retaining API serialization.
- Existing frontend-facing response keys remain unchanged; model, ocean, and discovery provenance is derived from the selected dataset metadata.
- JSON remains the default, and the frontend was not modified.

## Prototype 2.1 Phase 3 milestone
- Added `NetCDFDatasetRegistry` and `DatasetDescriptor` for startup discovery and validation of local NetCDF files.
- Unsupported or invalid files are skipped with warnings; valid descriptors record provider, variable, coverage, time, depth, and filename metadata.
- Copernicus repository candidates are selected by variable and requested coverage, with opened datasets reused by path for the application lifetime.
- Provider selection, discovery, validation, and failures emit concise backend log records.
- The API and frontend contracts remain unchanged, and explicit Phase 2 file-path configuration remains supported.

## Prototype 2.1.5 Phase 1 milestone
- Replaced implicit provider capabilities with one explicit `BaseOceanRepository` contract implemented by JSON and Copernicus providers.
- `OceanDataService` uses only formal provider methods; runtime `getattr()` capability detection was removed.
- Added shared provider exceptions while preserving compatible API error behavior.

## Prototype 2.1.5 Phase 2 milestone
- Added `DatasetBundle` as the canonical scientific dataset identity model.
- Registry discovery now stores bundles rather than per-variable path descriptors.
- Factory and Copernicus repositories receive and retain bundles, including source files and metadata.
- Existing explicit path construction remains compatible, and public API behavior is unchanged.
