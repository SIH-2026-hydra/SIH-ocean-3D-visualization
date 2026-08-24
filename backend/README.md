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
