from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ocean_basic_query():
    response = client.get('/api/v1/ocean')
    assert response.status_code == 200
    payload = response.json()
    assert payload['query']['parameter'] == 'temperature'
    assert payload['metadata']['count'] > 0
    assert len(payload['data']) > 0


def test_ocean_temperature_query():
    response = client.get('/api/v1/ocean?parameter=temperature&depth=100')
    assert response.status_code == 200
    payload = response.json()
    assert payload['query']['parameter'] == 'temperature'
    assert all('value' in item for item in payload['data'])
    assert all(item['value'] is not None for item in payload['data'])


def test_ocean_salinity_query():
    response = client.get('/api/v1/ocean?parameter=salinity&depth=50')
    assert response.status_code == 200
    payload = response.json()
    assert payload['query']['parameter'] == 'salinity'
    assert all('value' in item for item in payload['data'])
    assert all(item['value'] is not None for item in payload['data'])


def test_ocean_current_query_returns_vector_and_speed():
    response = client.get('/api/v1/ocean?parameter=current&depth=0')
    assert response.status_code == 200
    payload = response.json()
    assert payload['query']['parameter'] == 'current'
    assert payload['metadata']['unit'] == 'm/s'
    assert all('current_u' in item and 'current_v' in item and 'speed' in item for item in payload['data'])
    assert all(item['speed'] >= 0 for item in payload['data'])


def test_ocean_current_speed_derived_product():
    response = client.get('/api/v1/ocean?parameter=current_speed&depth=0')
    assert response.status_code == 200
    payload = response.json()
    assert all(item['value'] >= 0 for item in payload['data'])
    assert payload['metadata']['derivedProduct'] == 'Current speed'
    assert payload['metadata']['units'] == 'm/s'
    assert payload['metadata']['sourceVariables'] == ['current_u', 'current_v']


def test_ocean_current_direction_derived_product():
    response = client.get('/api/v1/ocean?parameter=current_direction&depth=0')
    assert response.status_code == 200
    payload = response.json()
    assert all(0 <= item['value'] < 360 for item in payload['data'])
    assert payload['metadata']['derivedProduct'] == 'Current direction'
    assert payload['metadata']['units'] == 'degrees'


def test_raw_current_response_remains_vector_compatible():
    payload = client.get('/api/v1/ocean?parameter=current&depth=0').json()
    assert 'current_u' in payload['data'][0]
    assert 'current_v' in payload['data'][0]
    assert 'speed' in payload['data'][0]


def test_ocean_depth_filter():
    response = client.get('/api/v1/ocean?parameter=temperature&depth=200')
    assert response.status_code == 200
    payload = response.json()
    assert all(item['depth'] == 200 for item in payload['data'])


def test_ocean_timestamp_filter():
    response = client.get('/api/v1/ocean?parameter=temperature&time=2026-08-24T06:00:00Z')
    assert response.status_code == 200
    payload = response.json()
    assert all(item['timestamp'] == '2026-08-24T06:00:00Z' for item in payload['data'])


def test_ocean_geographic_bounds_filter():
    response = client.get('/api/v1/ocean?parameter=temperature&min_lat=10&max_lat=15&min_lon=55&max_lon=70')
    assert response.status_code == 200
    payload = response.json()
    assert len(payload['data']) > 0
    for item in payload['data']:
        assert 10 <= item['latitude'] <= 15
        assert 55 <= item['longitude'] <= 70


def test_ocean_viewport_query_returns_only_requested_cells():
    response = client.get('/api/v1/ocean?min_lat=10&max_lat=15&min_lon=55&max_lon=65')
    assert response.status_code == 200
    payload = response.json()
    assert payload['metadata']['returnedCellCount'] == len(payload['data'])
    assert all(10 <= item['latitude'] <= 15 and 55 <= item['longitude'] <= 65 for item in payload['data'])


def test_ocean_depth_interval_query():
    response = client.get('/api/v1/ocean?min_depth=50&max_depth=200')
    assert response.status_code == 200
    assert all(50 <= item['depth'] <= 200 for item in response.json()['data'])


def test_ocean_time_interval_query():
    response = client.get('/api/v1/ocean?start_time=2026-08-24T06:00:00Z&end_time=2026-08-24T12:00:00Z')
    assert response.status_code == 200
    assert {item['timestamp'] for item in response.json()['data']} == {
        '2026-08-24T08:00:00Z',
        '2026-08-24T12:00:00Z',
    }


def test_ocean_spatial_sampling_returns_every_nth_grid_point():
    baseline = client.get('/api/v1/ocean?depth=0').json()
    sampled_response = client.get('/api/v1/ocean?depth=0&sampling_factor=2')
    assert sampled_response.status_code == 200
    sampled = sampled_response.json()
    assert sampled['metadata']['samplingFactor'] == 2
    assert len(sampled['data']) < len(baseline['data'])
    assert {(item['latitude'], item['longitude']) for item in sampled['data']} <= {
        (item['latitude'], item['longitude']) for item in baseline['data']
    }


def test_ocean_query_metadata_describes_returned_fields():
    metadata = client.get('/api/v1/ocean?parameter=salinity&depth=100').json()['metadata']
    assert metadata['variable'] == 'salinity'
    assert metadata['units'] == 'PSU'
    assert metadata['gridResolution']
    assert metadata['returnedCellCount'] > 0
    assert metadata['samplingFactor'] == 1


def test_ocean_rejects_reverse_query_intervals():
    assert client.get('/api/v1/ocean?min_depth=200&max_depth=50').status_code == 400
    assert client.get('/api/v1/ocean?start_time=2026-08-24T12:00:00Z&end_time=2026-08-24T06:00:00Z').status_code == 400


def test_ocean_combined_filters():
    response = client.get(
        '/api/v1/ocean?parameter=salinity&depth=100&time=2026-08-24T12:00:00Z&min_lat=10&max_lat=20&min_lon=60&max_lon=80'
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload['data']) > 0
    for item in payload['data']:
        assert item['depth'] == 100
        assert item['timestamp'] == '2026-08-24T12:00:00Z'
        assert 10 <= item['latitude'] <= 20
        assert 60 <= item['longitude'] <= 80


def test_ocean_invalid_parameter():
    response = client.get('/api/v1/ocean?parameter=chlorophyll')
    assert response.status_code == 400


def test_ocean_invalid_latitude_and_longitude():
    response = client.get('/api/v1/ocean?lat=91')
    assert response.status_code == 400
    response = client.get('/api/v1/ocean?min_lat=10&max_lat=5')
    assert response.status_code == 400
    response = client.get('/api/v1/ocean?min_lon=50&max_lon=30')
    assert response.status_code == 400
    response = client.get('/api/v1/ocean?min_lon=-181')
    assert response.status_code == 400


def test_ocean_no_data_query():
    response = client.get('/api/v1/ocean?parameter=temperature&min_lat=50&max_lat=55&min_lon=100&max_lon=110')
    assert response.status_code == 200
    payload = response.json()
    assert payload['data'] == []
    assert payload['metadata']['count'] == 0


def test_ocean_point_query():
    response = client.get('/api/v1/ocean/point?lat=12.5&lon=60.0&depth=100&time=2026-08-24T00:00:00Z')
    assert response.status_code == 200
    payload = response.json()
    assert payload['requestedLocation']['latitude'] == 12.5
    assert payload['requestedLocation']['longitude'] == 60.0
    assert payload['depth'] == 100
    assert payload['timestamp'] == '2026-08-24T00:00:00Z'
    assert payload['model']['temperature'] is not None
    assert payload['source']['sourceType'] in {'model', 'synthetic', 'demo'}
    assert payload['observation'] is None
    assert payload['prediction'] is None


def test_ocean_point_outside_coverage():
    response = client.get('/api/v1/ocean/point?lat=45&lon=90&depth=200&time=2026-08-24T00:00:00Z')
    assert response.status_code == 404


def test_ocean_point_below_local_seafloor_is_unavailable():
    response = client.get('/api/v1/ocean/point?lat=10&lon=55&depth=8000&time=2026-08-24T00:00:00Z')
    assert response.status_code == 400
    assert 'below the local seafloor' in response.json()['detail']


def test_metadata_exposes_ocean_discovery():
    response = client.get('/api/v1/metadata')
    assert response.status_code == 200
    payload = response.json()
    assert 'discovery' in payload
    discovery = payload['discovery']
    assert 'parameters' in discovery
    assert 'units' in discovery
    assert 'depths' in discovery
    assert 'timestamps' in discovery
    assert 'spatialCoverage' in discovery
    assert 'dataset' in discovery
    assert discovery['synthetic'] is True
