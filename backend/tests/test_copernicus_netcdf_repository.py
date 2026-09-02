from datetime import datetime, timezone

import numpy as np
import pytest

xr = pytest.importorskip('xarray')

from app.repositories.copernicus_netcdf_repository import CopernicusNetCDFRepository
from app.core.config import Settings
from app.repositories.factory import create_repository
from app.repositories.netcdf_registry import NetCDFDatasetRegistry
from app.services.ocean_data_service import OceanDataService


@pytest.fixture
def local_copernicus_files(tmp_path):
    coordinates = {
        'time': np.array(['2026-09-01T00:00:00', '2026-09-01T06:00:00'], dtype='datetime64[ns]'),
        'depth': [0.494025, 47.374, 92.326],
        'latitude': [10.0, 12.5, 15.0],
        'longitude': [70.0, 72.5, 75.0],
    }
    shape = (2, 3, 3, 3)
    values = np.arange(np.prod(shape), dtype=float).reshape(shape)
    values[0, 1, 1, 1] = np.nan
    paths = {}
    definitions = {
        'temperature': ('thetao', 'degC', values + 20),
        'salinity': ('so', '1e-3', values + 30),
        'current_u': ('uo', 'm s-1', values / 100),
        'current_v': ('vo', 'm s-1', values / 200),
    }
    for field, (variable, unit, data) in definitions.items():
        path = tmp_path / f'{field}.nc'
        xr.Dataset({variable: (tuple(coordinates), data, {'units': unit})}, coords=coordinates).to_netcdf(path)
        paths[field] = path
    return paths


def test_normalizes_variables_coordinates_depth_time_and_provenance(local_copernicus_files):
    with CopernicusNetCDFRepository(local_copernicus_files) as repository:
        records = repository.get_ocean_records(
            parameter='temperature',
            depth=50,
            timestamp='2026-09-01T01:00:00Z',
            min_lat=10,
            max_lat=11,
            min_lon=72,
            max_lon=73,
        )

    assert len(records) == 1
    record = records[0]
    assert record['temperature'] == pytest.approx(30.0)
    assert record['depth'] == pytest.approx(47.374)
    assert record['requested_depth'] == 50
    assert record['matched_depth'] == pytest.approx(47.374)
    assert record['timestamp'] == '2026-09-01T00:00:00Z'
    assert record['source_type'] == 'model'
    assert record['provider'] == 'Copernicus Marine'
    assert record['is_synthetic'] is False


def test_maps_currents_derives_speed_and_preserves_missing_as_none(local_copernicus_files):
    with CopernicusNetCDFRepository(local_copernicus_files) as repository:
        records = repository.get_ocean_records(parameter='current', depth=0.494025)

    first = records[0]
    assert first['current_u'] is not None
    assert first['current_v'] is not None
    assert first['current_speed'] == pytest.approx((first['current_u'] ** 2 + first['current_v'] ** 2) ** 0.5)

    missing = next(record for record in records if record['latitude'] == 12.5 and record['longitude'] == 72.5)
    assert missing['current_u'] is not None

    with CopernicusNetCDFRepository(local_copernicus_files) as repository:
        temperature = repository.get_ocean_records(parameter='temperature')
    missing_temperature = next(
        record for record in temperature
        if record['latitude'] == 12.5 and record['longitude'] == 72.5 and record['depth'] == pytest.approx(47.374)
    )
    assert missing_temperature['temperature'] is None


def test_metadata_is_real_and_out_of_coverage_is_empty(local_copernicus_files):
    with CopernicusNetCDFRepository(local_copernicus_files) as repository:
        metadata = repository.get_dataset_metadata()[0]
        records = repository.get_ocean_records(parameter='salinity', min_lat=50)

    assert metadata['source'] == 'Copernicus Marine'
    assert metadata['source_type'] == 'model'
    assert metadata['is_synthetic'] is False
    assert metadata['spatial_coverage']['min_latitude'] == 10.0
    assert records == []


def test_timestamp_accepts_aware_datetime(local_copernicus_files):
    with CopernicusNetCDFRepository(local_copernicus_files) as repository:
        records = repository.get_ocean_records(
            parameter='salinity',
            timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )

    assert records
    assert {record['timestamp'] for record in records} == {'2026-09-01T00:00:00Z'}


def test_factory_selects_json_and_copernicus_without_api_changes(local_copernicus_files):
    json_repository = create_repository(Settings(ocean_provider='json'))
    copernicus_repository = create_repository(Settings(
        ocean_provider='copernicus',
        copernicus_temperature_path=str(local_copernicus_files['temperature']),
    ))

    assert json_repository.__class__.__name__ == 'JsonOceanRepository'
    assert isinstance(copernicus_repository, CopernicusNetCDFRepository)
    copernicus_repository.close()


def test_api_contract_switches_to_copernicus_provider(monkeypatch, local_copernicus_files):
    from fastapi.testclient import TestClient

    from app.api.v1.endpoints import metadata, model, ocean
    from app.main import app

    repository = CopernicusNetCDFRepository(local_copernicus_files)
    monkeypatch.setattr(ocean, 'service', OceanDataService(repository))
    monkeypatch.setattr(model, 'service', OceanDataService(repository))
    monkeypatch.setattr(metadata, 'service', OceanDataService(repository))

    client = TestClient(app)
    response = client.get('/api/v1/ocean?parameter=temperature&depth=50&time=2026-09-01T00:00:00Z&min_lat=10&max_lat=10&min_lon=70&max_lon=70')
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {'query', 'metadata', 'data'}
    assert payload['metadata']['sourceType'] == 'model'
    assert payload['metadata']['isSynthetic'] is False
    assert payload['data'][0]['value'] is not None
    assert payload['data'][0]['depth'] == pytest.approx(47.374)

    point = client.get('/api/v1/ocean/point?lat=12.5&lon=72.5&depth=50&time=2026-09-01T00:00:00Z')
    assert point.status_code == 200
    point_payload = point.json()
    assert set(point_payload) == {'requestedLocation', 'matchedLocation', 'depth', 'timestamp', 'model', 'observation', 'prediction', 'source'}
    assert point_payload['source']['isSynthetic'] is False
    assert point_payload['depth'] == pytest.approx(47.374)

    discovery = client.get('/api/v1/metadata').json()['discovery']
    assert discovery['synthetic'] is False
    assert discovery['depths'] == pytest.approx([0.494025, 47.374, 92.326])
    repository.close()


def test_copernicus_out_of_range_query_returns_consistent_not_found(local_copernicus_files):
    service = OceanDataService(CopernicusNetCDFRepository(local_copernicus_files))
    with pytest.raises(LookupError, match='outside'):
        service.get_ocean_records(parameter='temperature', depth=50, min_lat=50, max_lat=51)


def test_registry_discovers_supported_files_and_skips_invalid(tmp_path, local_copernicus_files):
    for path in local_copernicus_files.values():
        target = tmp_path / path.name
        target.write_bytes(path.read_bytes())
    (tmp_path / 'notes.nc').write_text('not a NetCDF file', encoding='utf-8')

    registry = NetCDFDatasetRegistry(tmp_path)
    discovered = registry.discover()

    assert len(discovered) == 4
    assert {dataset.variable for dataset in discovered} == {'temperature', 'salinity', 'current_u', 'current_v'}
    assert all(dataset.provider == 'Copernicus Marine' for dataset in discovered)
    assert len(registry.by_variable('temperature')) == 1


def test_registry_registers_both_current_components_from_one_file(tmp_path, local_copernicus_files):
    current_u = xr.open_dataset(local_copernicus_files['current_u'])
    current_v = xr.open_dataset(local_copernicus_files['current_v'])
    combined = xr.merge([current_u, current_v])
    path = tmp_path / 'currents.nc'
    combined.to_netcdf(path)
    current_u.close()
    current_v.close()
    combined.close()

    registry = NetCDFDatasetRegistry(tmp_path)
    registry.discover()

    assert {dataset.variable for dataset in registry.datasets if dataset.path == path} == {'current_u', 'current_v'}


def test_factory_discovers_data_directory_without_explicit_filenames(tmp_path, local_copernicus_files):
    for path in local_copernicus_files.values():
        target = tmp_path / path.name
        target.write_bytes(path.read_bytes())

    repository = create_repository(Settings(ocean_provider='copernicus', copernicus_data_dir=str(tmp_path)))
    try:
        assert isinstance(repository, CopernicusNetCDFRepository)
        assert repository.get_ocean_records(parameter='temperature', depth=50)
    finally:
        repository.close()


def test_provider_selects_second_dataset_for_covered_request(tmp_path, local_copernicus_files):
    first = local_copernicus_files['temperature']
    second = tmp_path / 'temperature_second.nc'
    dataset = xr.open_dataset(first)
    dataset = dataset.assign_coords(latitude=[30.0, 32.5, 35.0])
    dataset.to_netcdf(second)
    dataset.close()

    repository = CopernicusNetCDFRepository({'temperature': [first, second]})
    try:
        records = repository.get_ocean_records(parameter='temperature', min_lat=30, max_lat=35)
    finally:
        repository.close()

    assert records
    assert min(record['latitude'] for record in records) == 30.0