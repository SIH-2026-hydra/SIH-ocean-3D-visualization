import { createPointQuery } from '../utils/location.js';

export const API_BASE_URL =
  import.meta.env?.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';

function buildQueryString(params) {
  const entries = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);

  return entries.length ? `?${entries.join('&')}` : '';
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = payload?.detail || payload?.message || 'API request failed.';
    throw new Error(message);
  }

  return payload;
}

export async function getOceanData({
  parameter = 'temperature',
  depth,
  time,
  minLat,
  maxLat,
  minLon,
  maxLon,
  source,
  signal,
} = {}) {
  const query = buildQueryString({
    parameter,
    depth,
    time,
    min_lat: minLat,
    max_lat: maxLat,
    min_lon: minLon,
    max_lon: maxLon,
    source,
  });

  return requestJson(`${API_BASE_URL}/ocean${query}`, { signal });
}

export function buildOceanPointUrl({
  lat,
  lon,
  depth,
  time,
} = {}) {
  const point = createPointQuery({ lat, lon }, depth, time);
  if (!point) return null;
  const query = buildQueryString({ lat: point.latitude, lon: point.longitude, depth: point.depth, time: point.time });
  return `${API_BASE_URL}/ocean/point${query}`;
}

export async function getOceanPoint(params = {}) {
  const url = buildOceanPointUrl(params);
  if (!url) throw new TypeError('A valid latitude, longitude, depth, and time are required for an ocean point request.');
  return requestJson(url, { signal: params.signal });
}

export async function getOceanMetadata() {
  return requestJson(`${API_BASE_URL}/metadata`);
}
