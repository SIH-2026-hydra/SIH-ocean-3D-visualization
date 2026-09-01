"""Service layer for ML predictions using a deterministic prototype predictor."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from app.repositories.base import BaseOceanRepository
from app.services.bathymetry_service import BathymetryService


class PrototypePredictor:
    """Deterministic prototype predictor used solely for Phase 9A.
    
    This service establishes the production ML prediction contract without requiring
    a trained neural network or heavy ML dependencies. Predictions are deterministic
    (same input → same output) and derived through a lightweight feature-based
    transformation.
    
    Prototype 2 will replace this with predictions from real trained models on global data.
    """

    MODEL_ID = 'prototype-predictor-v1'
    MODEL_VERSION = '1.0'
    PREDICTION_TYPE = 'prototype'
    SOURCE = 'prototype-ml-prediction'
    IS_EXPERIMENTAL = True

    def predict(
        self,
        *,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: datetime | str,
    ) -> dict[str, Any] | None:
        """Predict ocean state at a specific point.
        
        This class intentionally uses its own feature transformation instead of
        returning numerical model records. It has no fitting or training path.
        """
        # Normalize timestamp
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                return None
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        # Generate deterministic prototype prediction
        temperature = self._predict_temperature(
            latitude, longitude, depth, timestamp
        )
        salinity = self._predict_salinity(latitude, longitude, depth, timestamp)
        current_u, current_v = self._predict_current(
            latitude, longitude, depth, timestamp
        )
        current_speed = (
            math.sqrt(current_u ** 2 + current_v ** 2)
            if current_u is not None and current_v is not None
            else None
        )

        return {
            'latitude': latitude,
            'longitude': longitude,
            'depth': depth,
            'timestamp': timestamp.isoformat().replace('+00:00', 'Z'),
            'temperature': temperature,
            'salinity': salinity,
            'current_u': current_u,
            'current_v': current_v,
            'current_speed': current_speed,
            'model_id': self.MODEL_ID,
            'model_version': self.MODEL_VERSION,
            'prediction_type': self.PREDICTION_TYPE,
            'source': self.SOURCE,
            'is_experimental': self.IS_EXPERIMENTAL,
        }

    def _predict_temperature(
        self,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: datetime,
    ) -> float:
        """Deterministic temperature prediction based on geographic/temporal features.
        
        Uses a synthetic feature-based model that produces realistic ocean temperature behavior:
        - Warm surface (equator-biased)
        - Cold at depth
        - Seasonal variation
        """
        # Base temperature: latitude-dependent warm at equator, cool poleward
        latitude_factor = abs(latitude - 15.0) / 30.0  # Strongest at 15°N
        base_temp = 28.0 - (latitude_factor ** 1.5) * 15.0

        # Depth attenuation: exponential cooling with depth
        depth_factor = math.exp(-depth / 250.0)
        depth_adjusted = base_temp * depth_factor + 4.0

        # Temporal variation (seasonal): low-frequency modulation
        day_of_year = timestamp.timetuple().tm_yday
        seasonal_phase = (day_of_year / 365.25) * 2 * math.pi
        seasonal_variation = 2.5 * math.sin(seasonal_phase)

        # Longitude-based variation (e.g., currents)
        lon_factor = math.sin((longitude - 45.0) / 50.0 * math.pi)
        lon_variation = lon_factor * 1.5

        prediction = depth_adjusted + seasonal_variation + lon_variation

        # Clamp to realistic range
        return max(0.5, min(32.0, prediction))

    def _predict_salinity(
        self,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: datetime,
    ) -> float:
        """Deterministic salinity prediction."""
        # Base salinity: relatively stable with subtle variation
        base_salinity = 35.0

        # Latitude effect (river discharge, evaporation)
        lat_effect = math.sin((latitude - 15.0) / 30.0 * math.pi) * 0.3

        # Depth effect: salinity increases slightly with depth (stratification)
        depth_effect = math.tanh(depth / 500.0) * 0.5

        # Temporal variation
        day_of_year = timestamp.timetuple().tm_yday
        seasonal_phase = (day_of_year / 365.25) * 2 * math.pi
        temporal_variation = 0.2 * math.cos(seasonal_phase + 0.5)

        # Longitude variation
        lon_effect = math.sin((longitude - 70.0) / 50.0 * math.pi) * 0.2

        prediction = (
            base_salinity + lat_effect + depth_effect + temporal_variation + lon_effect
        )

        # Clamp to realistic range
        return max(33.0, min(37.0, prediction))

    def _predict_current(
        self,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: datetime,
    ) -> tuple[float, float]:
        """Deterministic current (U, V) prediction."""
        # Current magnitude decreases with depth
        depth_factor = math.exp(-depth / 500.0)

        # Base current pattern: illustrative seasonal gyre simulation
        base_magnitude = 0.4 * depth_factor

        # Latitude-dependent flow direction
        lat_sine = math.sin((latitude - 15.0) / 20.0 * math.pi)
        lat_cosine = math.cos((latitude - 15.0) / 20.0 * math.pi)

        # Longitude-dependent modulation
        lon_sine = math.sin((longitude - 70.0) / 25.0 * math.pi)

        # Temporal variation
        day_of_year = timestamp.timetuple().tm_yday
        seasonal_phase = (day_of_year / 365.25) * 2 * math.pi
        seasonal_factor = 0.5 + 0.5 * math.cos(seasonal_phase)

        # Combine components
        u = (
            base_magnitude * lat_sine * lon_sine * seasonal_factor
        )
        v = (
            base_magnitude * lat_cosine * (1.0 - abs(lon_sine)) * seasonal_factor
        )

        # Add small deterministic noise (seeded by coordinates/time for reproducibility)
        u += 0.05 * math.sin(latitude * longitude * timestamp.timestamp())
        v += 0.05 * math.cos(latitude * longitude * timestamp.timestamp())

        return (u, v)


class PredictionService:
    """Validates prediction requests and delegates inference to a predictor.

    Keeping this orchestration separate lets Prototype 2 replace
    ``PrototypePredictor`` without changing the API or frontend contract.
    """

    def __init__(self, repository: BaseOceanRepository, predictor: PrototypePredictor | None = None) -> None:
        self.repository = repository
        self.predictor = predictor or PrototypePredictor()
        self.bathymetry_service = BathymetryService(repository)

    def predict_point(
        self,
        *,
        latitude: float,
        longitude: float,
        depth: float,
        timestamp: datetime | str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if not self._is_within_model_coverage(latitude, longitude):
            return None, 'outside_coverage'

        bathymetry = self.bathymetry_service.get_point_bathymetry(latitude, longitude)
        if bathymetry and depth > float(bathymetry['seafloor_depth']):
            return None, 'below_seafloor'

        prediction = self.predictor.predict(
            latitude=latitude,
            longitude=longitude,
            depth=depth,
            timestamp=timestamp,
        )
        return prediction, None

    def _is_within_model_coverage(self, latitude: float, longitude: float) -> bool:
        metadata = self.repository.get_dataset_metadata()
        coverage = metadata[0].get('spatial_coverage', {}) if metadata else {}
        return (
            float(coverage.get('min_latitude', -90.0)) <= latitude <= float(coverage.get('max_latitude', 90.0))
            and float(coverage.get('min_longitude', -180.0)) <= longitude <= float(coverage.get('max_longitude', 180.0))
        )
