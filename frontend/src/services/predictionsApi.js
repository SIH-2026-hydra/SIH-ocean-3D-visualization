import { API_BASE_URL } from './api';

function query(params) {
  return Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');
}

async function request(url, signal) {
  const response = await fetch(url, { signal });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || 'Prediction request failed.');
  return payload;
}

export function getPointPrediction({ lat, lon, depth, time, signal }) {
  return request(
    `${API_BASE_URL}/predictions/point?${query({ lat, lon, depth, time })}`,
    signal
  );
}
