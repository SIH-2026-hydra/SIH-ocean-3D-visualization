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


def test_startup_initializes_provider_and_shutdown_closes_it(monkeypatch):
    provider = FakeProvider()
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: provider)
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
    dependencies.close_repository()

    with TestClient(app) as client:
        payload = client.get('/api/v1/health').json()
        assert payload['provider_ready'] is True
        assert payload['registry_ready'] is False


def test_repeated_startup_shutdown_closes_each_provider(monkeypatch):
    providers = [FakeProvider(), FakeProvider()]
    created = iter(providers)
    monkeypatch.setattr(dependencies, 'create_repository', lambda settings: next(created))
    dependencies.close_repository()

    with TestClient(app):
        assert dependencies.repository.provider_ready is True
    with TestClient(app):
        assert dependencies.repository.provider_ready is True

    assert all(provider.close_calls == 1 for provider in providers)
