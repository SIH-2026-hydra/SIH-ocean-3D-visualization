const TEMPERATURE_STOPS = [
  { stop: 0, color: '#0d3b91' },
  { stop: 0.2, color: '#1e6cc7' },
  { stop: 0.4, color: '#4cb5d8' },
  { stop: 0.6, color: '#8ad7b8' },
  { stop: 0.8, color: '#f5d66d' },
  { stop: 1, color: '#ff694d' },
];

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function interpolateColor(startHex, endHex, ratio) {
  const start = startHex.replace('#', '');
  const end = endHex.replace('#', '');

  const toRGB = (hex) => {
    const normalized = hex.length === 3
      ? hex.split('').map((part) => part + part).join('')
      : hex;
    return {
      r: Number.parseInt(normalized.slice(0, 2), 16),
      g: Number.parseInt(normalized.slice(2, 4), 16),
      b: Number.parseInt(normalized.slice(4, 6), 16),
    };
  };

  const startRGB = toRGB(start);
  const endRGB = toRGB(end);

  const mixChannel = (a, b) => Math.round(a + (b - a) * ratio);
  const red = mixChannel(startRGB.r, endRGB.r);
  const green = mixChannel(startRGB.g, endRGB.g);
  const blue = mixChannel(startRGB.b, endRGB.b);

  return `rgb(${red}, ${green}, ${blue})`;
}

export function getTemperatureColor(value, min, max) {
  if (!Number.isFinite(value)) return 'rgba(255,255,255,0.1)';

  const safeMin = Number.isFinite(min) ? min : value;
  const safeMax = Number.isFinite(max) && max > safeMin ? max : safeMin + 1;

  const normalized = clamp((value - safeMin) / (safeMax - safeMin), 0, 1);

  if (normalized <= 0) return TEMPERATURE_STOPS[0].color;
  if (normalized >= 1) return TEMPERATURE_STOPS[TEMPERATURE_STOPS.length - 1].color;

  for (let index = 0; index < TEMPERATURE_STOPS.length - 1; index += 1) {
    const current = TEMPERATURE_STOPS[index];
    const next = TEMPERATURE_STOPS[index + 1];

    if (normalized >= current.stop && normalized <= next.stop) {
      const span = next.stop - current.stop || 1;
      const ratio = (normalized - current.stop) / span;
      return interpolateColor(current.color, next.color, ratio);
    }
  }

  return TEMPERATURE_STOPS[TEMPERATURE_STOPS.length - 1].color;
}

export function getTemperatureRange(values) {
  const numericValues = values
    .filter((entry) => Number.isFinite(Number(entry)))
    .map((entry) => Number(entry));

  if (!numericValues.length) {
    return { min: 0, max: 0 };
  }

  const min = Math.min(...numericValues);
  const max = Math.max(...numericValues);
  return { min, max };
}

export function formatTemperature(value) {
  if (!Number.isFinite(Number(value))) return 'n/a';
  return Number(value).toFixed(1);
}

export function getTemperatureScaleStops() {
  return [...TEMPERATURE_STOPS];
}
