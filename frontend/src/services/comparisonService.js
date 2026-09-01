const isFiniteNumber = (value) => (
  value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
);

const currentSpeed = (u, v) => (
  isFiniteNumber(u) && isFiniteNumber(v) ? Math.hypot(Number(u), Number(v)) : null
);

const metric = ({ parameter, unit, observationValue, modelValue, predictionValue }) => {
  const modelAvailable = isFiniteNumber(observationValue) && isFiniteNumber(modelValue);
  const predictionAvailable = isFiniteNumber(observationValue) && isFiniteNumber(predictionValue);
  const modelDifference = modelAvailable ? Number(modelValue) - Number(observationValue) : null;
  const predictionDifference = predictionAvailable ? Number(predictionValue) - Number(observationValue) : null;
  const modelAbsoluteError = modelAvailable ? Math.abs(modelDifference) : null;
  const predictionAbsoluteError = predictionAvailable ? Math.abs(predictionDifference) : null;

  let closerEstimate = null;
  if (modelAbsoluteError != null && predictionAbsoluteError != null) {
    if (Math.abs(modelAbsoluteError - predictionAbsoluteError) < 1e-12) closerEstimate = 'tie';
    else closerEstimate = modelAbsoluteError < predictionAbsoluteError ? 'model' : 'prediction';
  }

  return {
    parameter,
    unit,
    observationValue: isFiniteNumber(observationValue) ? Number(observationValue) : null,
    modelValue: isFiniteNumber(modelValue) ? Number(modelValue) : null,
    modelDifference,
    modelAbsoluteError,
    predictionValue: isFiniteNumber(predictionValue) ? Number(predictionValue) : null,
    predictionDifference,
    predictionAbsoluteError,
    available: modelAvailable || predictionAvailable,
    closerEstimate,
  };
};

/**
 * Build a point-wise comparison without mutating any scientific source payload.
 * This is not an aggregate accuracy evaluation; it only compares a valid nearby
 * observation with the model and prototype-prediction values at one selection.
 */
export function buildPointComparison({ model, observation, prediction }) {
  if (!observation) {
    return {
      available: false,
      reason: 'no_suitable_observation',
      reference: null,
      metrics: [],
    };
  }

  const observationSpeed = currentSpeed(observation.current_u, observation.current_v);
  const predictionSpeed = prediction?.current_speed ?? currentSpeed(prediction?.current_u, prediction?.current_v);
  const metrics = [
    metric({ parameter: 'Temperature', unit: '°C', observationValue: observation.temperature, modelValue: model?.temperature, predictionValue: prediction?.temperature }),
    metric({ parameter: 'Salinity', unit: 'PSU', observationValue: observation.salinity, modelValue: model?.salinity, predictionValue: prediction?.salinity }),
    metric({ parameter: 'Current Speed', unit: 'm/s', observationValue: observationSpeed, modelValue: model?.currentSpeed, predictionValue: predictionSpeed }),
  ].filter((item) => item.observationValue != null);

  return {
    available: metrics.some((item) => item.available),
    reason: metrics.some((item) => item.available) ? null : 'no_shared_measurements',
    reference: 'observation',
    metrics,
  };
}
