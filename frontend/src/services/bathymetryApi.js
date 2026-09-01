/**
 * Bathymetry API service for static geographic seafloor depth queries.
 * Does not depend on time, depth, or parameter state.
 */

import { API_BASE_URL } from './api';

export async function getBathymetryPoint(latitude, longitude, signal) {
  if (typeof latitude !== 'number' || typeof longitude !== 'number') {
    throw new Error('Latitude and longitude must be numbers');
  }

  const response = await fetch(
    `${API_BASE_URL}/bathymetry/point?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`,
    {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal,
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      return null; // No bathymetry data at this location
    }
    throw new Error(`Bathymetry API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getBathymetryRegion(minLat, maxLat, minLon, maxLon) {
  const params = [
    ['min_lat', minLat],
    ['max_lat', maxLat],
    ['min_lon', minLon],
    ['max_lon', maxLon],
  ]
    .filter(([, value]) => value !== undefined)
    .map(([name, value]) => `${encodeURIComponent(name)}=${encodeURIComponent(value)}`)
    .join('&');

  const response = await fetch(`${API_BASE_URL}/bathymetry?${params}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Bathymetry API error: ${response.statusText}`);
  }

  return response.json();
}
