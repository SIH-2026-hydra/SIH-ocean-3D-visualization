/** Canonical application location shape: { latitude: number, longitude: number }. */
export function normalizeLocation(location) {
  if (!location || typeof location !== 'object') return null;

  const rawLatitude = location.latitude ?? location.lat;
  const rawLongitude = location.longitude ?? location.lon;
  if (rawLatitude === null || rawLatitude === undefined || rawLatitude === '' || rawLongitude === null || rawLongitude === undefined || rawLongitude === '') return null;
  const latitude = Number(rawLatitude);
  const longitude = Number(rawLongitude);
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return null;

  return { latitude, longitude };
}

export function createPointQuery(location, depth, time) {
  const normalizedLocation = normalizeLocation(location);
  const normalizedDepth = Number(depth);
  if (!normalizedLocation || !Number.isFinite(normalizedDepth) || normalizedDepth < 0 || typeof time !== 'string' || !time) {
    return null;
  }

  return { ...normalizedLocation, depth: normalizedDepth, time };
}

export function isCurrentPointContext(context, selectedLocation, selectedDepth, selectedTime) {
  const expected = createPointQuery(selectedLocation, selectedDepth, selectedTime);
  const actual = createPointQuery(context, context?.depth, context?.time);
  return Boolean(expected && actual
    && expected.latitude === actual.latitude
    && expected.longitude === actual.longitude
    && expected.depth === actual.depth
    && expected.time === actual.time);
}
