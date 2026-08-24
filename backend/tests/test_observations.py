from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_observations_endpoint_returns_records():
    response = client.get('/api/v1/observations')
    assert response.status_code == 200
    payload = response.json()
    assert 'data' in payload
    assert len(payload['data']) > 0


def test_observations_depth_filter_returns_only_matching_records():
    response = client.get('/api/v1/observations?depth=0')
    assert response.status_code == 200
    payload = response.json()
    depths = [item['depth'] for item in payload['data']]
    assert all(depth == 0 for depth in depths)


def test_metadata_endpoint_exposes_synthetic_status():
    response = client.get('/api/v1/metadata')
    assert response.status_code == 200
    payload = response.json()
    assert 'data' in payload
    assert len(payload['data']) > 0
    assert any(item.get('is_synthetic') is True for item in payload['data'])
