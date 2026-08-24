from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_model_endpoint_returns_records():
    response = client.get('/api/v1/model')
    assert response.status_code == 200
    payload = response.json()
    assert 'data' in payload
    assert len(payload['data']) > 0


def test_model_depth_filter_returns_only_matching_records():
    response = client.get('/api/v1/model?depth=100')
    assert response.status_code == 200
    payload = response.json()
    depths = [item['depth'] for item in payload['data']]
    assert all(depth == 100 for depth in depths)


def test_model_invalid_depth_filter_is_handled():
    response = client.get('/api/v1/model?depth=abc')
    assert response.status_code == 400
