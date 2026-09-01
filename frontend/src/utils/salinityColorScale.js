const SALINITY_STOPS = [
  { stop: 0, color: '#163b65' },
  { stop: 0.25, color: '#1f7890' },
  { stop: 0.5, color: '#57b69e' },
  { stop: 0.75, color: '#c4d77a' },
  { stop: 1, color: '#f3c66b' },
];

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

function interpolateColor(startHex, endHex, ratio) {
  const start = startHex.slice(1);
  const end = endHex.slice(1);
  const channel = (offset) => Math.round(parseInt(start.slice(offset, offset + 2), 16) + (parseInt(end.slice(offset, offset + 2), 16) - parseInt(start.slice(offset, offset + 2), 16)) * ratio);
  return `rgb(${channel(0)}, ${channel(2)}, ${channel(4)})`;
}

export function getSalinityColor(value, min, max) {
  if (!Number.isFinite(value)) return 'rgba(255,255,255,0.1)';
  const normalized = clamp((value - min) / ((max - min) || 1), 0, 1);
  for (let index = 0; index < SALINITY_STOPS.length - 1; index += 1) {
    const current = SALINITY_STOPS[index];
    const next = SALINITY_STOPS[index + 1];
    if (normalized <= next.stop) {
      return interpolateColor(current.color, next.color, (normalized - current.stop) / (next.stop - current.stop));
    }
  }
  return SALINITY_STOPS[SALINITY_STOPS.length - 1].color;
}

export function getSalinityScaleStops() {
  return [...SALINITY_STOPS];
}
