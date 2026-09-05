from fastapi.testclient import TestClient

from app.main import app
from app import dependencies


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['service'] == 'ocean-intelligence-api'


class FakeProvider:
    def __init__(self):
        self.close_calls = 0

    def close(self):
        self.close_calls += 1


def test_startup_initializes_explicit_provider_and_shutdown_closes_it(monkeypatch):
    provider = FakeProvider()
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: provider)
    monkeypatch.setattr(dependencies.settings, 'ocean_provider', 'json')
    monkeypatch.setattr(dependencies.settings, 'copernicus_acquisition_enabled', False)
    dependencies.close_repository()

    with TestClient(app) as client:
        assert dependencies.repository.provider_ready is True
        assert client.get('/api/v1/health').json()['provider_ready'] is True

    assert provider.close_calls == 1
    assert dependencies.repository.provider_ready is False


def test_readiness_reports_registry_state(monkeypatch):
    provider = FakeProvider()
    provider.registry = type('Registry', (), {'ready': False})()
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: provider)
    monkeypatch.setattr(dependencies.settings, 'ocean_provider', 'json')
    monkeypatch.setattr(dependencies.settings, 'copernicus_acquisition_enabled', False)
    dependencies.close_repository()

    with TestClient(app) as client:
        payload = client.get('/api/v1/health').json()
        assert payload['provider_ready'] is True
        assert payload['registry_ready'] is False


def test_repeated_startup_shutdown_closes_each_provider(monkeypatch):
    providers = [FakeProvider(), FakeProvider()]
    created = iter(providers)
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: next(created))
    monkeypatch.setattr(dependencies.settings, 'ocean_provider', 'json')
    monkeypatch.setattr(dependencies.settings, 'copernicus_acquisition_enabled', False)
    dependencies.close_repository()

    with TestClient(app):
        assert dependencies.repository.provider_ready is True
    with TestClient(app):
        assert dependencies.repository.provider_ready is True

    assert all(provider.close_calls == 1 for provider in providers)


def test_request_driven_startup_is_ready_without_selecting_a_provider(monkeypatch, caplog):
    created = []
    monkeypatch.setattr(dependencies.settings, 'ocean_provider', 'auto')
    monkeypatch.setattr(dependencies.settings, 'copernicus_acquisition_enabled', True)
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: created.append(True))
    dependencies.close_repository()

    with caplog.at_level('INFO'):
        with TestClient(app) as client:
            health = client.get('/api/v1/health').json()
            assert health['status'] == 'ok'
            assert health['provider_ready'] is False

    assert created == []
    assert 'waiting for scientific requests' in caplog.text


def test_restored_operational_cache_activates_provider_before_query(monkeypatch, tmp_path):
    class QueryableProvider(FakeProvider):
        def query_ocean_records(self, **_filters):
            return []

    provider = QueryableProvider()
    monkeypatch.setattr(dependencies.settings, 'ocean_provider', 'auto')
    monkeypatch.setattr(dependencies.settings, 'copernicus_acquisition_enabled', True)
    monkeypatch.setattr(dependencies.settings, 'copernicus_cache_dir', str(tmp_path))
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: provider)
    dependencies.close_repository()
    monkeypatch.setattr(dependencies, 'operational_data_manager', None)

    manager = dependencies.get_operational_data_manager()
    assert manager is not None
    assert dependencies.repository.provider_ready is False

    manager.on_available()

    assert dependencies.repository.provider_ready is True
    assert dependencies.repository.query_ocean_records(parameter='temperature') == []
    dependencies.close_repository()


def test_request_driven_nonquery_endpoints_do_not_dereference_an_unbound_provider(monkeypatch):
    created = []
    monkeypatch.setattr(dependencies.settings, 'ocean_provider', 'auto')
    monkeypatch.setattr(dependencies.settings, 'copernicus_acquisition_enabled', True)
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: created.append(True))
    dependencies.close_repository()

    with TestClient(app) as client:
        responses = {
            path: client.get(path)
            for path in (
                '/api/v1/datasets', '/api/v1/variables', '/api/v1/coverage',
                '/api/v1/capabilities', '/api/v1/metadata', '/api/v1/bathymetry',
                '/api/v1/observations',
                '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z',
                '/api/v1/model', '/api/v1/bathymetry/point?lat=15&lon=70',
            )
        }

    assert all(response.status_code != 503 for response in responses.values())
    assert all(responses[path].status_code == 200 for path in (
        '/api/v1/datasets', '/api/v1/variables', '/api/v1/coverage',
        '/api/v1/capabilities', '/api/v1/metadata', '/api/v1/bathymetry',
        '/api/v1/observations',
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z',
    ))
    assert responses['/api/v1/model'].status_code == 404
    assert responses['/api/v1/bathymetry/point?lat=15&lon=70'].status_code == 404
    assert created == []
