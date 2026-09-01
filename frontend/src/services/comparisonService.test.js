import assert from 'node:assert/strict';
import test from 'node:test';

import { buildPointComparison } from './comparisonService.js';

const sources = {
  model: { temperature: 28.92, salinity: 35.2, currentSpeed: 0.5 },
  observation: { temperature: 28.7, salinity: 35.0, current_u: 0.3, current_v: 0.4 },
  prediction: { temperature: 28.61, salinity: 35.4, current_u: 0.1, current_v: 0.2 },
};

test('calculates signed differences, absolute errors, and the closer estimate', () => {
  const comparison = buildPointComparison(sources);
  const temperature = comparison.metrics[0];
  assert.ok(Math.abs(temperature.modelDifference - 0.22) < 1e-12);
  assert.ok(Math.abs(temperature.modelAbsoluteError - 0.22) < 1e-12);
  assert.ok(Math.abs(temperature.predictionDifference + 0.09) < 1e-12);
  assert.ok(Math.abs(temperature.predictionAbsoluteError - 0.09) < 1e-12);
  assert.equal(temperature.closerEstimate, 'prediction');
});

test('compares salinity and current speed only when present', () => {
  const comparison = buildPointComparison(sources);
  const salinity = comparison.metrics[1];
  const current = comparison.metrics[2];
  assert.equal(salinity.parameter, 'Salinity');
  assert.equal(current.observationValue, 0.5);
  assert.equal(current.modelDifference, 0);
  assert.equal(current.closerEstimate, 'model');
});

test('does not fabricate values when observations or individual variables are absent', () => {
  assert.deepEqual(buildPointComparison({ model: sources.model, prediction: sources.prediction, observation: null }), {
    available: false, reason: 'no_suitable_observation', reference: null, metrics: [],
  });
  const comparison = buildPointComparison({ ...sources, observation: { temperature: 20 } });
  assert.equal(comparison.metrics.length, 1);
  assert.equal(comparison.metrics[0].modelValue, 28.92);
  assert.equal(comparison.metrics[0].predictionValue, 28.61);
  const missingSources = buildPointComparison({ observation: { temperature: 20 }, model: {}, prediction: {} });
  assert.equal(missingSources.metrics[0].modelValue, null);
  assert.equal(missingSources.metrics[0].predictionValue, null);
});

test('reports ties when both absolute errors are equal', () => {
  const comparison = buildPointComparison({
    model: { temperature: 11 }, observation: { temperature: 10 }, prediction: { temperature: 9 },
  });
  assert.equal(comparison.metrics[0].closerEstimate, 'tie');
});
