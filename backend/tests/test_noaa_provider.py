from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.models.dataset_bundle import DatasetBundle
from app.repositories import NOAAOceanRepository
from app.repositories.base import BaseOceanRepository
from app.repositories.factory import create_repository


def test_noaa_provider_implements_existing_contract():
    repository = NOAAOceanRepository()
    try:
        assert isinstance(repository, BaseOceanRepository)
        assert isinstance(repository.dataset_bundles[0], DatasetBundle)
        assert repository.dataset_bundles[0].provider == 'NOAA'
        assert {
            'query_ocean_records',
            'query_ocean_point',
            'get_provider_capabilities',
            'health',
            'get_model_records',
            'get_observation_records',
            'get_dataset_metadata',
            'get_bathymetry_records',
            'close',
        } <= set(dir(repository))
    finally:
        repository.close()


def test_factory_switches_to_noaa_provider():
    repository = create_repository(Settings(ocean_provider='noaa'))
    try:
        assert isinstance(repository, NOAAOceanRepository)
        assert repository.get_provider_capabilities()['provider'] == 'NOAA'
    finally:
        repository.close()


def test_noaa_supports_existing_queries_and_derived_products(monkeypatch):
    from app import dependencies

    previous = dependencies.repository._repository
    repository = NOAAOceanRepository()
    dependencies.repository.set(repository)
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: repository)
    try:
        client = TestClient(app)
        response = client.get(
            '/api/v1/ocean?parameter=current_direction&min_lat=10&max_lat=20&min_lon=50&max_lon=70&min_depth=0&max_depth=100&sampling_factor=2'
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload['metadata']['derivedProduct'] == 'Current direction'
        assert payload['metadata']['sourceVariables'] == ['current_u', 'current_v']
        assert payload['data']
        assert all(0 <= item['value'] < 360 for item in payload['data'])
        assert client.get('/api/v1/datasets').json()['datasets'][0]['provider'] == 'NOAA'
        assert 'NOAA' in client.get('/api/v1/capabilities').json()['capabilities']['supported_providers']
    finally:
        repository.close()
        if previous is not None:
            dependencies.repository.set(previous)
        else:
            dependencies.repository.clear()
