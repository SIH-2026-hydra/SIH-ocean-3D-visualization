import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getCapabilityDiscovery,
  getCoverageDiscovery,
  getDatasetCatalog,
  getVariableDiscovery,
} from './api.js';

const originalFetch = globalThis.fetch;

test.afterEach(() => {
  globalThis.fetch = originalFetch;
});

test('discovery clients request the backend catalog surfaces', async () => {
  const requested = [];
  globalThis.fetch = async (url) => {
    requested.push(url);
    return { ok: true, json: async () => ({}) };
  };

  await getDatasetCatalog();
  await getVariableDiscovery();
  await getCoverageDiscovery();
  await getCapabilityDiscovery();

  assert.deepEqual(requested.map((url) => url.split('/').at(-1)), [
    'datasets', 'variables', 'coverage', 'capabilities',
  ]);
});
