"""Tests for bathymetry endpoints and service."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.json_repository import JsonOceanRepository
from app.services.bathymetry_service import BathymetryService

client = TestClient(app)


@pytest.fixture
def bathymetry_service() -> BathymetryService:
    """Fixture providing a bathymetry service instance."""
    repo = JsonOceanRepository()
    return BathymetryService(repo)


class TestBathymetryService:
    """Unit tests for BathymetryService."""

    def test_get_bathymetry_records(self, bathymetry_service: BathymetryService) -> None:
        """Test fetching all bathymetry records."""
        records = bathymetry_service.get_bathymetry_records()
        assert isinstance(records, list)
        assert len(records) > 0
        assert all('seafloor_depth' in r for r in records)
        assert all('latitude' in r for r in records)
        assert all('longitude' in r for r in records)

    def test_filter_records_by_latitude(self, bathymetry_service: BathymetryService) -> None:
        """Test filtering bathymetry by latitude bounds."""
        records = bathymetry_service.get_bathymetry_records()
        filtered = bathymetry_service.filter_records(records, min_lat=10.0, max_lat=20.0)
        
        assert all(10.0 <= r['latitude'] <= 20.0 for r in filtered)
        assert len(filtered) > 0
        assert len(filtered) < len(records)

    def test_filter_records_by_longitude(self, bathymetry_service: BathymetryService) -> None:
        """Test filtering bathymetry by longitude bounds."""
        records = bathymetry_service.get_bathymetry_records()
        filtered = bathymetry_service.filter_records(records, min_lon=50.0, max_lon=70.0)
        
        assert all(50.0 <= r['longitude'] <= 70.0 for r in filtered)
        assert len(filtered) > 0

    def test_filter_records_combined_bounds(self, bathymetry_service: BathymetryService) -> None:
        """Test filtering bathymetry with combined lat/lon bounds."""
        records = bathymetry_service.get_bathymetry_records()
        filtered = bathymetry_service.filter_records(
            records,
            min_lat=5.0,
            max_lat=15.0,
            min_lon=45.0,
            max_lon=65.0,
        )
        
        assert all(5.0 <= r['latitude'] <= 15.0 for r in filtered)
        assert all(45.0 <= r['longitude'] <= 65.0 for r in filtered)

    def test_find_nearest_point(self, bathymetry_service: BathymetryService) -> None:
        """Test finding nearest bathymetry record to a point."""
        records = bathymetry_service.get_bathymetry_records()
        nearest = bathymetry_service.find_nearest_point(records, 10.0, 55.0)
        
        assert nearest is not None
        assert 'seafloor_depth' in nearest
        assert isinstance(nearest['seafloor_depth'], (int, float))

    def test_find_nearest_point_empty_records(self, bathymetry_service: BathymetryService) -> None:
        """Test find_nearest_point with empty record list."""
        nearest = bathymetry_service.find_nearest_point([], 10.0, 55.0)
        assert nearest is None

    def test_get_point_bathymetry(self, bathymetry_service: BathymetryService) -> None:
        """Test querying bathymetry at a specific point."""
        result = bathymetry_service.get_point_bathymetry(10.0, 55.0)
        
        assert result is not None
        assert 'requested_location' in result
        assert 'matched_location' in result
        assert 'seafloor_depth' in result
        assert 'source' in result
        assert 'is_synthetic' in result
        assert result['is_synthetic'] is True

    def test_point_outside_provider_coverage_is_unavailable(self, bathymetry_service: BathymetryService) -> None:
        assert bathymetry_service.get_point_bathymetry(0.0, 0.0) is None


class TestBathymetryEndpoints:
    """Integration tests for bathymetry API endpoints."""

    def test_bathymetry_regional_query(self) -> None:
        """Test regional bathymetry query endpoint."""
        response = client.get(
            '/api/v1/bathymetry',
            params={
                'min_lat': '10.0',
                'max_lat': '20.0',
                'min_lon': '50.0',
                'max_lon': '70.0',
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert 'count' in data
        assert 'total' in data
        assert len(data['data']) > 0

    def test_bathymetry_point_query(self) -> None:
        """Test point bathymetry query endpoint."""
        response = client.get(
            '/api/v1/bathymetry/point',
            params={'lat': '10.0', 'lon': '55.0'},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'requested_location' in data
        assert 'matched_location' in data
        assert 'seafloor_depth' in data
        assert data['is_synthetic'] is True

    def test_bathymetry_point_query_missing_parameters(self) -> None:
        """Test point query with missing latitude/longitude."""
        response = client.get('/api/v1/bathymetry/point', params={'lat': '10.0'})
        assert response.status_code == 422  # FastAPI returns 422 for missing required parameters

    def test_bathymetry_point_outside_coverage(self) -> None:
        response = client.get('/api/v1/bathymetry/point', params={'lat': '0.0', 'lon': '0.0'})
        assert response.status_code == 404

    def test_bathymetry_invalid_latitude(self) -> None:
        """Test bathymetry query with invalid latitude."""
        response = client.get(
            '/api/v1/bathymetry/point',
            params={'lat': '150.0', 'lon': '55.0'},
        )
        assert response.status_code == 400

    def test_bathymetry_invalid_longitude(self) -> None:
        """Test bathymetry query with invalid longitude."""
        response = client.get(
            '/api/v1/bathymetry/point',
            params={'lat': '10.0', 'lon': '250.0'},
        )
        assert response.status_code == 400

    def test_bathymetry_invalid_bounds(self) -> None:
        """Test regional query with invalid bounds."""
        response = client.get(
            '/api/v1/bathymetry',
            params={
                'min_lat': '20.0',
                'max_lat': '10.0',  # inverted
            },
        )
        assert response.status_code == 400

    def test_bathymetry_empty_region(self) -> None:
        """Test regional query with no matching data."""
        response = client.get(
            '/api/v1/bathymetry',
            params={
                'min_lat': '70.0',
                'max_lat': '80.0',
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 0

    def test_bathymetry_depth_values_plausible(self) -> None:
        """Test that bathymetry depths are plausible for ocean."""
        response = client.get(
            '/api/v1/bathymetry',
            params={'min_lat': '5.0', 'max_lat': '30.0'},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Plausible ocean depths should be between 100m and 7000m
        for record in data['data']:
            assert 100 <= record['seafloor_depth'] <= 7000

    def test_bathymetry_coordinate_consistency(self) -> None:
        """Test that requested and matched locations are close."""
        response = client.get(
            '/api/v1/bathymetry/point',
            params={'lat': '12.5', 'lon': '57.5'},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        req_lat = data['requested_location']['latitude']
        req_lon = data['requested_location']['longitude']
        match_lat = data['matched_location']['latitude']
        match_lon = data['matched_location']['longitude']
        
        # Matched should be close to requested (within ~10 degrees for demo)
        assert abs(match_lat - req_lat) < 10.0
        assert abs(match_lon - req_lon) < 10.0

    def test_bathymetry_synthetic_flag(self) -> None:
        """Test that bathymetry records are marked as synthetic for demo."""
        response = client.get(
            '/api/v1/bathymetry/point',
            params={'lat': '10.0', 'lon': '55.0'},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_synthetic'] is True
        assert 'synthetic' in data['source'].lower()
