# Development Log

## Backend Phase 1 (Complete)

Completed:
- FastAPI foundation
- Windows .venv setup
- normalized schemas
- JSON repository
- ocean-data service
- demo dataset
- health endpoint
- model endpoint
- observation endpoint
- metadata endpoint
- tests

Test status:
- **7 passed** in 0.40s
- All Phase 1 endpoints validated
- Depth filtering tested
- Invalid input handling verified
- Synthetic data status exposed

Known issues:
- None

## Backend Phase 2 (Ocean Data Engine Complete)

Completed:
- Generic ocean-state API contract for temperature, salinity, and current vectors
- Spatial/depth/time filtering in service layer before serialization
- Global-capable normalized records with explicit synthetic provenance
- /api/v1/ocean and /api/v1/ocean/point endpoints
- Metadata discovery payload for parameters, units, depths, timestamps, and coverage
- Deterministic demo grid generator for Indian Ocean coverage with smooth depth/time variation
- Preserved existing model/observation endpoints and Phase 1 behavior

Coverage:
- 6 latitudes x 6 longitudes x 5 depths x 6 timestamps = 1080 model records
- Geographic demo domain: 5°N–30°N, 45°E–95°E
- Depths: 0, 50, 100, 200, 500 m
- Timestamps: 2026-08-24T00:00:00Z to 2026-08-24T20:00:00Z at 4-hour intervals

Test status:
- **21 passed** in 0.55s
- Ocean queries, point lookups, bounding-box logic, metadata discovery, and Phase 1 compatibility validated

Known issues:
- No real observations or ML predictions are populated in this phase; those remain null by contract
- No scientific interpolation or deferred visualization yet

## Frontend Infrastructure Phase 1 (Complete)

Completed:
- Vite + React project structure
- package.json with React 18, Vite 5, CesiumJS 1.120
- vite.config.js with React plugin
- ESLint configuration for React and Vite
- index.html with React root div
- Environment variable templates (.env.example)
- .gitignore for node_modules, dist, .env
- Frontend README with full Windows setup instructions
- Cesium asset configuration for Vite
- Global geographic architecture documented
- Indian Ocean default demo viewport documented
- Reserved component structure for frontend AI
- No placeholder UI or demo code created

Known issues:
- None

Test status:
- Infrastructure configuration complete
- npm install/build verification deferred (Node.js not available in current environment)
- Full verification can proceed when Node.js/npm become available: `cd frontend && npm install && npm run lint`

## Frontend Phase 5 (Depth Exploration Complete)

Completed:
- Shared selectedDepth state across the depth control, temperature API, temperature layer, legend, and point inspector
- Metadata-driven discrete depths with Surface / 0 m default and demo fallback depths
- Abortable temperature and point requests to prevent stale rapid-switch results
- Selected marker location preserved while point values refresh at the new depth

Verification:
- Editor diagnostics pass for the Phase 5 frontend files
- npm lint/build and runtime verification require a working Node/npm shell

## Next milestone

Frontend AI tool to implement Phase 1 Cesium globe:
- Global Earth rendering
- Initial Indian Ocean camera position
- Rotation, zoom, pan navigation
- Home/Reset action
- Then proceed to backend integration and ocean data visualization

## Frontend Phase 6 (Time Exploration Complete)

Completed:
- Shared metadata-backed selectedTime state for the timeline, temperature field, legend, and selected point inspector
- Discrete UTC slider with timestep markers, previous/next controls, and play/pause playback that stops at the final timestep
- Existing abortable request flow reused for rapid timeline changes without stale temperature or point results
- Two-level temporal navigation: efficient available-date selector plus selected-date discrete time slider
- Chronological previous/next and playback cross UTC date boundaries without preloading scientific data

Verification:
- Editor diagnostics pass for the Phase 6 frontend files
- npm lint/build and runtime verification require a working Node/npm shell

## Frontend Phase 7 (Salinity + Ocean Current Visualization)

Completed:
- Shared selectedParameter control for temperature, salinity, and current
- Reusable ScalarFieldLayer with the existing temperature color scale and a distinct salinity scale
- Static, subsampled current vectors using backend current_u/current_v values and derived speed
- Parameter-aware legend while retaining the complete point inspector state

Verification:
- Editor diagnostics pass for Phase 7 frontend files
- npm lint/build and runtime verification require a working Node/npm shell
