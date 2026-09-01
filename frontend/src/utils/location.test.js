import assert from 'node:assert/strict';
import test from 'node:test';

import { createPointQuery, isCurrentPointContext, normalizeLocation } from './location.js';
import { buildOceanPointUrl } from '../services/api.js';

test('normalizes globe and observation coordinates into one canonical shape', () => {
  assert.deepEqual(normalizeLocation({ latitude: 18.3, longitude: 70.4 }), { latitude: 18.3, longitude: 70.4 });
  assert.deepEqual(normalizeLocation({ lat: '18.3', lon: '70.4' }), { latitude: 18.3, longitude: 70.4 });
});

test('rejects invalid locations instead of creating a malformed point query', () => {
  assert.equal(normalizeLocation({ latitude: undefined, longitude: 70 }), null);
  assert.equal(normalizeLocation({ latitude: Number.NaN, longitude: 70 }), null);
  assert.equal(normalizeLocation({ latitude: null, longitude: 70 }), null);
  assert.equal(createPointQuery({ latitude: 18, longitude: undefined }, 50, '2026-08-24T00:00:00Z'), null);
});

test('ocean point URL includes coordinates or is not constructed', () => {
  const url = buildOceanPointUrl({ lat: 18.3, lon: 70.4, depth: 50, time: '2026-08-24T04:00:00Z' });
  assert.match(url, /lat=18.3/);
  assert.match(url, /lon=70.4/);
  assert.equal(buildOceanPointUrl({ depth: 50, time: '2026-08-24T04:00:00Z' }), null);
});

test('preserves coordinates across time and depth query changes', () => {
  const location = normalizeLocation({ latitude: 18.3, longitude: 70.4 });
  assert.deepEqual(createPointQuery(location, 0, '2026-08-24T00:00:00Z'), { latitude: 18.3, longitude: 70.4, depth: 0, time: '2026-08-24T00:00:00Z' });
  assert.deepEqual(createPointQuery(location, 500, '2026-08-24T20:00:00Z'), { latitude: 18.3, longitude: 70.4, depth: 500, time: '2026-08-24T20:00:00Z' });
});

test('rejects comparison payloads from a different selected point context', () => {
  const selected = { latitude: 18.3, longitude: 70.4 };
  assert.equal(isCurrentPointContext({ ...selected, depth: 50, time: '2026-08-24T04:00:00Z' }, selected, 50, '2026-08-24T04:00:00Z'), true);
  assert.equal(isCurrentPointContext({ ...selected, depth: 0, time: '2026-08-24T04:00:00Z' }, selected, 50, '2026-08-24T04:00:00Z'), false);
});
