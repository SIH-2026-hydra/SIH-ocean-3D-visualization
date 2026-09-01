"""Tests for ML prediction service and API."""

import math

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_point_prediction_deterministic():
    """Verify prediction is deterministic (same input → same output)."""
    response1 = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    response2 = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()['prediction'] == response2.json()['prediction']


def test_point_prediction_valid_response_structure():
    """Verify prediction response contains required fields."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'requested_location' in payload
    assert 'requested_depth' in payload
    assert 'requested_time' in payload
    assert 'available' in payload
    assert 'prediction' in payload

    if payload['available']:
        prediction = payload['prediction']
        assert 'latitude' in prediction
        assert 'longitude' in prediction
        assert 'depth' in prediction
        assert 'timestamp' in prediction
        assert 'temperature' in prediction
        assert 'salinity' in prediction
        assert 'current_u' in prediction
        assert 'current_v' in prediction
        assert 'current_speed' in prediction
        assert 'model_id' in prediction
        assert 'model_version' in prediction
        assert 'source' in prediction
        assert 'is_experimental' in prediction


def test_point_prediction_temperature_range():
    """Verify temperature prediction is within plausible range."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=0&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    prediction = response.json()['prediction']
    if prediction:
        temp = prediction['temperature']
        assert 0.0 <= temp <= 35.0  # Plausible ocean temperature


def test_point_prediction_salinity_range():
    """Verify salinity prediction is within plausible range."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    prediction = response.json()['prediction']
    if prediction:
        salinity = prediction['salinity']
        assert 32.0 <= salinity <= 38.0  # Plausible ocean salinity


def test_point_prediction_current_speed_consistency():
    """Verify current speed matches sqrt(U² + V²)."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    prediction = response.json()['prediction']
    if prediction and prediction.get('current_u') is not None and prediction.get('current_v') is not None:
        u = prediction['current_u']
        v = prediction['current_v']
        speed = prediction['current_speed']
        expected_speed = math.sqrt(u ** 2 + v ** 2)
        assert abs(speed - expected_speed) < 0.0001


def test_point_prediction_depth_variation():
    """Verify temperature decreases with depth."""
    response_surface = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=0&time=2026-08-24T00:00:00Z'
    )
    response_deep = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=500&time=2026-08-24T00:00:00Z'
    )
    assert response_surface.status_code == 200
    assert response_deep.status_code == 200

    surface_temp = response_surface.json()['prediction']['temperature']
    deep_temp = response_deep.json()['prediction']['temperature']
    assert surface_temp > deep_temp  # Temperature should decrease with depth


def test_point_prediction_temporal_variation():
    """Verify prediction changes with time (seasonal variation)."""
    response_jan = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-01-15T00:00:00Z'
    )
    response_jul = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-07-15T00:00:00Z'
    )
    assert response_jan.status_code == 200
    assert response_jul.status_code == 200

    temp_jan = response_jan.json()['prediction']['temperature']
    temp_jul = response_jul.json()['prediction']['temperature']
    assert temp_jan != temp_jul  # Should have seasonal variation


def test_point_prediction_invalid_latitude():
    """Verify prediction rejects invalid latitude."""
    response = client.get(
        '/api/v1/predictions/point?lat=91&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 422  # Unprocessable entity


def test_point_prediction_invalid_longitude():
    """Verify prediction rejects invalid longitude."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=181&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 422


def test_point_prediction_negative_depth():
    """Verify prediction rejects negative depth."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=-10&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 400
    assert 'depth' in response.json()['detail'].lower()


def test_point_prediction_invalid_timestamp():
    """Verify prediction rejects invalid timestamp."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=not-a-date'
    )
    assert response.status_code == 400


def test_point_prediction_experiment_metadata():
    """Verify prediction is clearly marked as experimental/prototype."""
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    prediction = response.json()['prediction']
    if prediction:
        assert prediction['is_experimental'] is True
        assert 'prototype' in prediction['source'].lower()
        assert 'v1' in prediction['model_version'].lower() or '1' in prediction['model_version']


def test_point_prediction_works_without_observation():
    """Verify prediction works even when no observation exists nearby."""
    observation_response = client.get(
        '/api/v1/observations/nearest?lat=7&lon=50&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert observation_response.status_code == 200
    assert observation_response.json()['available'] is False

    response = client.get(
        '/api/v1/predictions/point?lat=7&lon=50&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    assert response.json()['available'] is True


def test_point_prediction_multiple_locations():
    """Verify predictions vary across different locations."""
    response_loc1 = client.get(
        '/api/v1/predictions/point?lat=10&lon=60&depth=100&time=2026-08-24T00:00:00Z'
    )
    response_loc2 = client.get(
        '/api/v1/predictions/point?lat=25&lon=80&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response_loc1.status_code == 200
    assert response_loc2.status_code == 200

    temp1 = response_loc1.json()['prediction']['temperature']
    temp2 = response_loc2.json()['prediction']['temperature']
    # Predictions should differ across locations
    assert temp1 != temp2


def test_point_prediction_outside_supported_coverage_is_unavailable():
    response = client.get(
        '/api/v1/predictions/point?lat=40&lon=70&depth=100&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    assert response.json()['available'] is False
    assert response.json()['unavailable_reason'] == 'outside_coverage'


def test_point_prediction_below_seafloor_is_unavailable():
    response = client.get(
        '/api/v1/predictions/point?lat=15&lon=70&depth=10000&time=2026-08-24T00:00:00Z'
    )
    assert response.status_code == 200
    assert response.json()['available'] is False
    assert response.json()['unavailable_reason'] == 'below_seafloor'
