from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_observation_listing_and_provenance():
    response = client.get('/api/v1/observations')
    assert response.status_code == 200
    payload = response.json()
    assert payload['metadata']['isSynthetic'] is True
    assert len(payload['data']) == 6
    assert {'observation_id', 'platform_id', 'platform_type', 'quality', 'source', 'is_synthetic'} <= payload['data'][0].keys()


def test_observation_geographic_time_and_depth_filters():
    response = client.get('/api/v1/observations?min_lat=12&max_lat=13&min_lon=60&max_lon=61&time=2026-08-24T04:00:00Z&depth=100')
    assert response.status_code == 200
    assert response.json()['metadata']['count'] == 1
    assert response.json()['data'][0]['observation_id'] == 'obs-002'


def test_observation_parameter_and_platform_filters_and_missing_values():
    response = client.get('/api/v1/observations?parameter=salinity&platform_type=buoy')
    assert response.status_code == 200
    assert all(item['salinity'] is not None and item['platform_type'] == 'buoy' for item in response.json()['data'])
    response = client.get('/api/v1/observations?time=2026-08-24T20:00:00Z')
    assert response.status_code == 200
    assert response.json()['data'][0]['salinity'] is None


def test_nearest_observation_within_tolerances():
    response = client.get('/api/v1/observations/nearest?lat=12.9&lon=60.5&depth=100&time=2026-08-24T04:00:00Z')
    assert response.status_code == 200
    assert response.json()['available'] is True
    assert response.json()['observation']['observation_id'] == 'obs-002'


def test_nearest_observation_returns_clean_no_match_outside_tolerances():
    response = client.get('/api/v1/observations/nearest?lat=40&lon=20&depth=100&time=2026-08-24T04:00:00Z')
    assert response.status_code == 200
    assert response.json()['available'] is False
    assert response.json()['observation'] is None


def test_observation_invalid_coordinate_and_parameter():
    assert client.get('/api/v1/observations/nearest?lat=91&lon=60&depth=0&time=2026-08-24T00:00:00Z').status_code == 422
    assert client.get('/api/v1/observations?parameter=oxygen').status_code == 400
