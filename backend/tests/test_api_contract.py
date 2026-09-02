import pytest
from fastapi.testclient import TestClient

from app.api.limits import ResponseLimitExceededError, enforce_response_limits
from app.api.v1.endpoints import model
from app.main import app
from app.models.schemas import ApiErrorResponse, ModelResponse
from app.repositories.exceptions import DatasetUnavailableError


client = TestClient(app)


def test_response_models_validate_existing_payloads():
    payload = {
        'metadata': {'count': 1, 'sourceType': 'model', 'isSynthetic': True},
        'data': [{'latitude': 10, 'longitude': 20, 'depth': 0, 'timestamp': '2026-08-24T00:00:00Z', 'value': 25.0}],
    }
    response = ModelResponse.model_validate(payload)
    assert response.model_dump() == payload


def test_error_model_is_consistent_for_http_errors():
    response = client.get('/api/v1/model?depth=invalid')
    assert response.status_code == 400
    payload = response.json()
    validated = ApiErrorResponse.model_validate(payload)
    assert validated.detail == payload['detail']
    assert validated.error.code == 'http_error'


def test_oversized_response_is_rejected_without_truncation(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, 'max_response_cells', 1)
    response = client.get('/api/v1/model')
    assert response.status_code == 413
    payload = response.json()
    assert payload['error']['code'] == 'response_limit_exceeded'
    assert 'data' not in payload


def test_limit_utility_rejects_grid_dimensions(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, 'max_grid_dimension', 1)
    with pytest.raises(ResponseLimitExceededError) as error:
        enforce_response_limits({'data': [{'latitude': 1}, {'latitude': 2}]})
    assert error.value.limit == 'max_grid_dimension'


def test_provider_exception_maps_to_structured_error(monkeypatch):
    class FailingService:
        VALID_PARAMETERS = {'temperature', 'salinity', 'current'}

        def get_model_records(self, **kwargs):
            raise DatasetUnavailableError('missing provider data')

    monkeypatch.setattr(model, 'service', FailingService())
    response = client.get('/api/v1/model')
    assert response.status_code == 503
    assert response.json()['error']['code'] == 'http_error'


def test_existing_routes_have_explicit_response_models():
    paths = app.openapi()['paths']
    for path in (
        '/api/v1/health',
        '/api/v1/model',
        '/api/v1/ocean',
        '/api/v1/observations',
        '/api/v1/bathymetry',
        '/api/v1/predictions/point',
    ):
        assert '200' in paths[path]['get']['responses']
        assert 'content' in paths[path]['get']['responses']['200']
