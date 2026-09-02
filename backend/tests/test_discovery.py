from pathlib import Path

from fastapi.testclient import TestClient

from app.api.v1.endpoints import discovery
from app.main import app
from app.models.dataset_bundle import DatasetBundle
from app.services.discovery_service import DiscoveryService


class DiscoveryRepository:
    def __init__(self, bundles):
        self.dataset_bundles = tuple(bundles)

    def get_provider_capabilities(self):
        return {'provider': 'Test provider'}


def bundle(dataset_id, variables=('temperature',)):
    return DatasetBundle(
        dataset_id=dataset_id,
        provider='Test provider',
        product='test-product',
        model='test-model',
        forecast_cycle='2026-09-02T00:00:00Z',
        variables=variables,
        coordinate_signature=(('time', 'time'), ('depth', 'depth'), ('latitude', 'lat'), ('longitude', 'lon')),
        spatial_coverage={'min_latitude': 1.0, 'max_latitude': 2.0, 'min_longitude': 3.0, 'max_longitude': 4.0},
        temporal_coverage={'start': '2026-09-01T00:00:00Z', 'end': '2026-09-02T00:00:00Z'},
        depth_levels=(0.0, 100.0),
        source_files={'temperature': (Path('private.nc'),)},
        metadata={'source_variables': {'temperature': 'thetao'}},
    )


def test_dataset_catalog_serializes_bundle_without_paths():
    payload = DiscoveryService(DiscoveryRepository([bundle('one')])).catalog()
    assert payload[0]['dataset_id'] == 'one'
    assert payload[0]['available_variables'] == ['temperature']
    assert 'source_files' not in payload[0]
    assert 'private.nc' not in str(payload)


def test_multiple_bundles_and_empty_registry():
    service = DiscoveryService(DiscoveryRepository([bundle('one'), bundle('two', ('salinity',))]))
    assert [item['dataset_id'] for item in service.catalog()] == ['one', 'two']
    assert DiscoveryService(DiscoveryRepository([])).catalog() == []
    assert DiscoveryService(DiscoveryRepository([])).coverage() == []


def test_variable_discovery_includes_raw_and_derived_products():
    variables = DiscoveryService(DiscoveryRepository([bundle('one', ('current_u', 'current_v'))])).variables()
    by_name = {item['variable_name']: item for item in variables}
    assert by_name['current_u']['is_derived'] is False
    assert by_name['current_direction']['is_derived'] is True
    assert by_name['current_direction']['source_variables'] == ['current_u', 'current_v']
    assert by_name['current_direction']['units'] == 'degrees'


def test_coverage_and_capability_discovery():
    service = DiscoveryService(DiscoveryRepository([bundle('one')]))
    coverage = service.coverage()[0]
    assert coverage['spatial_coverage']['min_latitude'] == 1.0
    assert coverage['temporal_coverage']['start'] == '2026-09-01T00:00:00Z'
    assert coverage['depth_range'] == {'min': 0.0, 'max': 100.0}
    capabilities = service.capabilities()
    assert capabilities['interval_queries'] == {'depth': True, 'time': True}
    assert 'current_speed' in capabilities['derived_products']


def test_discovery_endpoints_and_existing_api_compatibility():
    client = TestClient(app)
    assert client.get('/api/v1/datasets').status_code == 200
    assert client.get('/api/v1/variables').status_code == 200
    assert client.get('/api/v1/coverage').status_code == 200
    assert client.get('/api/v1/capabilities').status_code == 200
    assert client.get('/api/v1/health').status_code == 200
    assert client.get('/api/v1/ocean?parameter=temperature').status_code == 200


def test_discovery_endpoint_uses_service_catalog(monkeypatch):
    monkeypatch.setattr(discovery.service, 'catalog', lambda: [DiscoveryService(DiscoveryRepository([bundle('one')])).catalog()[0]])
    response = TestClient(app).get('/api/v1/datasets')
    assert response.json()['datasets'][0]['dataset_id'] == 'one'
