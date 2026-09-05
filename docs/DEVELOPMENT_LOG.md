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

## Phase 9A / 9B (ML Point Prediction + Comparison)

Completed:
- Experimental deterministic ML point prediction is shown independently of model and observation state.
- A reusable frontend comparison service calculates point-wise signed differences and absolute errors only when a valid nearby observation exists.
- Temperature, salinity, and current-speed comparisons preserve missing values and explicitly report unavailable comparison states.

Limitations:
- This synthetic single-point diagnostic does not establish overall model or ML accuracy; aggregate MAE/RMSE, forecasting, and real-data integration remain out of scope.

## Prototype 2.1 Phase 1 (Offline Copernicus provider foundation)

Completed:
- Added an unregistered `CopernicusNetCDFRepository` for local NetCDF files.
- Normalized Copernicus `thetao`, `so`, `uo`, and `vo` to OCEANX model fields.
- Added current-speed derivation, coordinate subsetting, nearest time/depth matching, requested/matched depth metadata, NaN-to-null handling, and real model provenance.
- Added focused temporary-fixture tests with no network access.
- Added `xarray` and `netCDF4` backend dependencies.

Safety and scope:
- Existing endpoints continue using `JsonOceanRepository`; Prototype 1 synthetic behavior is unchanged.
- `real_data_test/`, NetCDF/Zarr files, credentials, and virtual environments remain ignored.
- Dynamic downloading, provider activation, caching, real observations, and global production queries remain out of scope.

Test status:
- Focused provider tests: **4 passed**

## Prototype 2.1 Phase 2 (Configurable provider integration)

Completed:
- Added `OCEAN_PROVIDER=json|copernicus` and local Copernicus path settings.
- Centralized repository construction in the application dependency module.
- Integrated provider-native nearest coordinate, time, and depth selection into `OceanDataService`.
- Preserved the existing frontend API response shapes and made model provenance provider-aware.
- Added factory, API switching, compatibility, and out-of-range integration tests.

Scope:
- JSON remains the default provider; no frontend changes were required.
- Downloading, caching, background jobs, authentication, and global production datasets remain out of scope.

Test status:
- Full backend suite: **67 passed**

## Prototype 2.2 Phase 4 (Dataset catalog and discovery APIs)

Completed:
- Added DatasetBundle-backed `/api/v1/datasets`, `/api/v1/variables`, `/api/v1/coverage`, and `/api/v1/capabilities` endpoints.
- Added `DiscoveryService` to translate retained registry bundles into public catalog and coverage responses without opening files or exposing paths.
- Added raw and derived variable discovery, including units, query support, and derived source variables.
- Preserved all existing routes, response payloads, provider abstractions, and scientific behavior.

Discovery flow:
`DatasetBundle registry -> repository -> DiscoveryService -> discovery API`

Test status:
- Full backend suite: **110 passed**

## Prototype 2.2 Phase 5 (Multi-provider integration)

Completed:
- Added `NOAAOceanRepository` as a local second scientific provider implementing the existing `BaseOceanRepository` contract.
- Registered NOAA through the existing `OCEAN_PROVIDER` configuration selection.
- Added canonical DatasetBundle metadata to both JSON and NOAA providers for provider-neutral discovery.
- Verified lifecycle, discovery, advanced queries, sampling, and derived products across provider implementations.

Provider flow:
`OCEAN_PROVIDER -> repository factory -> provider -> DatasetBundle -> service -> discovery/API`

Test status:
- Full backend suite: **113 passed**

## Indian Ocean Operational Platform Phase 1 (Complete frontend integration)

Completed:
- Added frontend clients for dataset, variable, coverage, and capability discovery APIs.
- Replaced hardcoded parameter, depth/time fallback, and geographic query configuration with backend discovery state.
- Added active DatasetBundle information panel with provider, product, forecast cycle, coverage, time, depth, and resolution context.
- Added first-class discovered derived-product layers for current speed and direction while preserving raw variable layers and request behavior.
- Updated legends and inspector context to use discovered variable names, units, dataset identity, provider, and provenance.

Frontend flow:
`Discovery APIs -> AppShell state -> controls/layers/legend/inspector -> existing ocean APIs`

Test status:
- Frontend tests: **10 passed**
- Backend suite: **113 passed**

## Prototype 2.1 Phase 3 (Local dataset pipeline)

Completed:
- Added automatic `*.nc` discovery from configurable `COPERNICUS_DATA_DIR`.
- Added startup validation and a registry of dataset identifiers, filenames, normalized/source variables, coverage, timestamps, and depths.
- Invalid or unsupported files are skipped with informative warnings.
- Added request-aware multi-dataset candidate selection and path-keyed in-memory dataset reuse.
- Preserved explicit Phase 2 file paths, JSON provider support, API schemas, and frontend compatibility.
- Added registry, invalid-file, startup discovery, and multi-dataset tests.

Startup flow:
`Settings -> NetCDFDatasetRegistry.discover() -> repository factory -> shared repository -> services -> existing API routes`

Test status:
- Phase 3 provider/registry tests: **11 passed**
- Full backend regression suite: **71 passed**

## Prototype 2.1.5 Phase 1 (Formal provider interface)

Completed:
- Formalized one `BaseOceanRepository` contract for collection queries, point queries, capabilities, health, and cleanup.
- Updated JSON and Copernicus providers to explicitly implement the same contract.
- Removed `getattr()` capability detection from `OceanDataService`.
- Added shared provider-layer exception types with built-in compatibility for existing API handlers.
- Added provider compliance, exception hierarchy, and no-dynamic-detection tests.

Test status:
- Focused contract tests: **14 passed**
- Full backend suite: pending final run

## Prototype 2.1.5 Phase 2 (DatasetBundle catalog)

Completed:
- Added `DatasetBundle` as the canonical dataset identity model.
- Registry discovery stores one bundle per validated file, including all supported variables in that file and their source paths.
- Factory passes discovered bundles to Copernicus repositories without reducing them to path lists.
- Repositories retain bundle identity and use bundle metadata for provider dataset metadata.
- Preserved explicit path compatibility, dataset selection behavior, scientific normalization, and public API schemas.
- Added bundle construction, registry, factory, repository, and identity-preservation tests.

Test status:
- Focused DatasetBundle tests: **15 passed**
- Full backend suite: pending final run

Remaining before Prototype 2.2:
- Production-scale data layout and query performance tuning, richer dataset identity/grouping, and operational monitoring.
- Downloading, scheduled jobs, distributed caching, cloud storage, and frontend real-data visualization remain out of scope.

## Indian Ocean Operational Transition (Phase 1)

Completed:
- Changed the default provider policy to `auto`, which chooses validated local Copernicus NetCDF bundles before the JSON development provider.
- Retained `OCEAN_PROVIDER=copernicus` as a strict real-data mode and `OCEAN_PROVIDER=json` as an explicit test/development mode.
- Reframed the frontend as OCEANX, the Indian Ocean Operational Platform, with backend-derived provider and model context instead of prototype badges.
- Kept DatasetBundle discovery as the sole source for the active dataset, coverage, time, depth, variables, units, and derived products.
- Suppressed fixture observations and prototype predictions for a Copernicus session; the inspector instead marks the future Argo/buoy observation integration point.

## Indian Ocean Operational Platform Sprint 2 (Operational Data Management)

Completed:
- Added an on-demand Operational Data Manager before Copernicus queries.
- Added provider/product/forecast-cycle/spatial/temporal cache matching, subset acquisition, NetCDF validation, and registry registration.
- Added repository refresh after successful registration so the existing query engine serves newly validated bundles without API changes.
- Added cache miss, cache hit, repeated request, spatial/temporal miss, registry, and serving regression tests.

Scope:
- Acquisition is opt-in and uses the Copernicus client only when enabled; no scheduled work, background worker, observation ingestion, or global download was added.

## Indian Ocean Operational Platform Sprint 3 (Request-Driven Data Management)

Completed:
- Replaced whole-Indian-Ocean automatic activation with request-addressable validated subsets.
- Extended the operational request and cache checks with depth range and requested source-resolution identity alongside provider, product, variables, viewport, time, and forecast cycle.
- Removed regional default acquisition: an enabled operational request must provide explicit viewport bounds.
- Added regression coverage for repeated viewport reuse, progressive viewport growth, temporal changes, depth changes, and request-dimension propagation.

## Indian Ocean Operational Platform Sprint 4 (Scientific Acquisition Framework)

Completed:
- Added provider-neutral scientific acquisition requests and an adapter-dispatching Acquisition Manager.
- Moved Copernicus SDK import, SDK request translation, provider dataset selection, and runtime error handling into a dedicated Copernicus adapter.
- Updated OperationalDataManager to delegate acquisition while retaining cache lookup, NetCDF validation, DatasetBundle registration, registry ownership, and repository refresh.
- Added framework dispatch, unknown-provider, Copernicus translation, provider-isolation, and runtime-failure tests.

## Indian Ocean Operational Platform Sprint 4.1 (Scientific Acquisition Runtime Completion)

Completed:
- Added automatic cache-directory creation and an atomic persistent manifest for validated DatasetBundles.
- Added deterministic request identity and concise cache/acquisition/validation/registration/refresh diagnostics.
- Restored cache bundles on manager restart without NetCDF revalidation or repeat acquisition.
- Added rollback of tentative registry entries when acquired data cannot satisfy the triggering request; failed acquisitions leave the persistent manifest untouched.

## Indian Ocean Operational Platform Sprint 4.2 (Request-Driven Runtime Activation)

Completed:
- Removed automatic provider selection and NetCDF discovery from `auto` startup when acquisition is enabled.
- Startup now reports ready and waits for scientific requests with no provider bound.
- OperationalDataManager remains the first-request activation path; only after it resolves cache/acquisition and registry registration is the normal query repository bound.
- Explicit JSON/Copernicus/NOAA selection and disabled-acquisition development behavior remain unchanged.

## Indian Ocean Operational Platform Sprint 4.5 (Backend Request-Driven Migration Completion)

- Completed the endpoint audit for deferred-provider access.
- Discovery, metadata, model, bathymetry, observation, and prediction paths now accept the intentionally unbound request-driven startup state.
- Platform endpoints return capability data or an empty/not-yet-acquired result without triggering provider selection or acquisition.
- Explicit viewport ocean requests remain responsible for cache/acquisition, registry, repository binding, and scientific queries.
