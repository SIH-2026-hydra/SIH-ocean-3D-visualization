# Ocean Intelligence Backend

## Requirements

- Windows 10/11
- Python 3.11+
- Git
- VS Code recommended

## Team setup checklist

- [ ] Clone repository
- [ ] Install/verify Python 3.11+
- [ ] Open repository in VS Code
- [ ] cd backend
- [ ] Create .venv
- [ ] Activate .venv
- [ ] Install requirements.txt
- [ ] Select .venv interpreter in VS Code
- [ ] Create .env from .env.example if needed
- [ ] Run FastAPI
- [ ] Open /api/v1/health
- [ ] Open /docs
- [ ] Run pytest
- [ ] Confirm tests pass

## Setup

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks script execution, use the Python launcher directly:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
python -m uvicorn app.main:app --reload
```

## Test

```powershell
python -m pytest
```

## API Documentation

Open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/api/v1/health

## Backend structure

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── data/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   └── main.py
├── tests/
├── .env.example
├── requirements.txt
├── README.md
└── .venv/
```

## Environment variables

The project reads values from `.env` when present. The file is optional because defaults are defined in the configuration module.

Example:

```env
APP_NAME=Ocean Intelligence API
APP_ENV=development
API_V1_PREFIX=/api/v1
HOST=127.0.0.1
PORT=8000
FRONTEND_ORIGIN=http://localhost:5173
```

## Demo-data status

This Phase 1 backend uses a deliberately small synthetic dataset in the Arabian Sea to validate the pipeline architecture. The data is annotated as synthetic and is not presented as real ocean observations.

## Current endpoints

- GET /api/v1/health
- GET /api/v1/model
- GET /api/v1/observations
- GET /api/v1/metadata

## Normalized data architecture

The backend keeps a consistent scientific contract across raw data sources:

JSON -> Repository -> Service -> FastAPI -> Frontend

This means later phases can replace the demo JSON files with NetCDF, APIs, or databases without forcing major frontend API changes.

### Provider contract

`BaseOceanRepository` is the single provider contract. JSON and Copernicus providers explicitly implement collection queries, point queries, metadata/capabilities, health, observation and bathymetry access, and lifecycle cleanup. `OceanDataService` calls this contract directly and does not inspect provider capabilities dynamically.

Provider failures use the shared hierarchy in `app.repositories.exceptions`: `ProviderError` is the base, with dataset-unavailable, provider-unavailable, invalid-query, unsupported-operation, and data-unavailable variants. These variants retain compatible built-in exception types so existing API error behavior is preserved.

## Prototype 2.1 offline provider

`CopernicusNetCDFRepository` is an additive repository for locally staged Copernicus NetCDF files. Configure paths by normalized field (`temperature`, `salinity`, `current_u`, `current_v`); it reads `thetao`, `so`, `uo`, and `vo`, preserves missing values as `None`, derives current speed, and reports Copernicus model provenance. It does not download data.

### Selecting the provider

The default is `OCEAN_PROVIDER=json`. Set `OCEAN_PROVIDER=copernicus` and configure one or more `COPERNICUS_*_PATH` values in `.env`; see `.env.example`. API modules receive the single configured repository from `app.dependencies`. `OceanDataService` delegates nearest selection to the Copernicus provider and keeps the existing response serialization, so the frontend does not know which provider is active.

Copernicus model data supplies model endpoints only. Observation and bathymetry collections remain empty unless separate providers are added later; the prototype predictor remains a separate experimental service. Missing provider files return a stable `503`, while out-of-range real point queries return `404`.

### Dataset discovery and registry

When `OCEAN_PROVIDER=copernicus` and `COPERNICUS_DATA_DIR` is set, application startup scans `COPERNICUS_FILE_PATTERN` (default `*.nc`). Each file is opened once for validation, and invalid or unsupported files are skipped with warnings so one bad file cannot stop the backend. Valid files become `DatasetDescriptor` entries containing the dataset identifier, filename, provider, normalized variable, source variable, coverage, timestamps, and depths.

The factory passes all discovered candidates to `CopernicusNetCDFRepository`. For each request, the provider chooses a candidate covering the requested variable, location, time, and depth. Open datasets are retained by path in the repository instance and closed explicitly with `close()` or a context manager. The repository is shared by API services through `app.dependencies`, avoiding per-request file opens.

Configuration options are:

- `OCEAN_PROVIDER`: `json` (default) or `copernicus`.
- `COPERNICUS_DATA_DIR`: directory scanned at startup; paths are local to the backend process.
- `COPERNICUS_FILE_PATTERN`: discovery glob, default `*.nc`.
- `COPERNICUS_VALIDATE_ON_STARTUP`: startup validation switch, default `true`.
- `COPERNICUS_LOG_LEVEL`: intended provider logging level, default `INFO`.
- `COPERNICUS_*_PATH`: optional explicit Phase 2 file paths, used when no data directory is configured.

Example:

```python
from app.repositories import CopernicusNetCDFRepository

repository = CopernicusNetCDFRepository({
	'temperature': '../real_data_test/temperature_depth_0_500.nc',
	'salinity': '../real_data_test/salinity.nc',
	'current_u': '../real_data_test/currents.nc',
	'current_v': '../real_data_test/currents.nc',
})
records = repository.get_ocean_records(parameter='temperature', depth=50)
repository.close()
```

## VS Code interpreter

Use the command palette:

- Ctrl + Shift + P
- Python: Select Interpreter
- backend/.venv/Scripts/python.exe

## Phase 1 limitations

- No real external ocean APIs yet
- No PostgreSQL or NetCDF integration yet
- No frontend rendering or 3D visualization yet
- No analytics or comparison logic beyond simple filtering and metadata exposure
