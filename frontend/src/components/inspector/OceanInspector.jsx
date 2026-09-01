import { useMemo } from 'react';
import './OceanInspector.css';

const formatCoordinate = (value) => {
  if (!Number.isFinite(Number(value))) return '—';
  return Number(value).toFixed(3);
};

const formatMetric = (value, digits = 2) => {
  if (!Number.isFinite(Number(value))) return '—';
  return Number(value).toFixed(digits);
};

const formatDepth = (value) => {
  if (!Number.isFinite(Number(value))) return '—';
  const numericDepth = Number(value);
  return numericDepth === 0 ? 'Surface · 0 m' : `${numericDepth.toFixed(0)} m`;
};

export default function OceanInspector({ selectedLocation, pointData, bathymetry, bathymetryUnavailable, observation, prediction, predictionUnavailableReason, loading, error, onClose }) {
  const requested = selectedLocation || pointData?.requestedLocation || {};
  const matched = pointData?.matchedLocation || {};
  const source = pointData?.source || {};

  const temperatureRows = useMemo(() => {
    const model = pointData?.model || {};
    return [
      { label: 'Temperature', value: model.temperature != null ? `${formatMetric(model.temperature, 2)} °C` : '—' },
      { label: 'Salinity', value: model.salinity != null ? `${formatMetric(model.salinity, 2)} PSU` : '—' },
    ];
  }, [pointData?.model]);

  const currentRows = useMemo(() => {
    const model = pointData?.model || {};
    return [
      { label: 'Speed', value: model.currentSpeed != null ? `${formatMetric(model.currentSpeed, 3)} m/s` : '—' },
      { label: 'U', value: model.currentU != null ? `${formatMetric(model.currentU, 3)} m/s` : '—' },
      { label: 'V', value: model.currentV != null ? `${formatMetric(model.currentV, 3)} m/s` : '—' },
    ];
  }, [pointData?.model]);

  const observationRows = useMemo(() => {
    if (!observation) return [];
    const platformType = observation.platform_type ? `${observation.platform_type[0].toUpperCase()}${observation.platform_type.slice(1)}` : 'Unavailable';
    const current = observation.current_u != null && observation.current_v != null
      ? `${formatMetric(Math.hypot(observation.current_u, observation.current_v), 3)} m/s`
      : 'Unavailable';
    return [
      { label: 'Platform', value: platformType },
      { label: 'Platform ID', value: observation.platform_id || 'Unavailable' },
      { label: 'Depth', value: formatDepth(observation.depth) },
      { label: 'Timestamp', value: observation.timestamp || 'Unavailable' },
      { label: 'Temperature', value: observation.temperature != null ? `${formatMetric(observation.temperature, 2)} °C` : 'Unavailable' },
      { label: 'Salinity', value: observation.salinity != null ? `${formatMetric(observation.salinity, 2)} PSU` : 'Unavailable' },
      { label: 'Current', value: current },
      { label: 'Quality', value: observation.quality || 'Unavailable' },
      { label: 'Source', value: observation.is_synthetic ? 'Demo/Synthetic' : (observation.source || 'Unavailable') },
    ];
  }, [observation]);

  const bathymetryRows = useMemo(() => {
    if (!bathymetry) return [];
    const seafloor = bathymetry.seafloor_depth ?? bathymetry.seafloorDepth;
    const selectedDepth = pointData?.depth ?? 0;
    const waterColumn = seafloor && Number.isFinite(selectedDepth) ? seafloor - selectedDepth : null;
    return [
      { label: 'Depth', value: seafloor ? `${formatMetric(seafloor, 0)} m` : '—' },
      { label: 'Water Column', value: waterColumn ? `${formatMetric(waterColumn, 0)} m` : '—' },
      { label: 'Source', value: bathymetry.is_synthetic ? 'Demo/Synthetic' : (bathymetry.source || '-') },
    ];
  }, [bathymetry, pointData?.depth]);

  const predictionRows = useMemo(() => {
    if (!prediction) return [];
    const current = prediction.current_u != null && prediction.current_v != null
      ? `${formatMetric(prediction.current_speed ?? Math.hypot(prediction.current_u, prediction.current_v), 3)} m/s`
      : 'Unavailable';
    return [
      { label: 'Temperature', value: prediction.temperature != null ? `${formatMetric(prediction.temperature, 2)} °C` : 'Unavailable' },
      { label: 'Salinity', value: prediction.salinity != null ? `${formatMetric(prediction.salinity, 2)} PSU` : 'Unavailable' },
      { label: 'Current Speed', value: current },
      { label: 'U', value: prediction.current_u != null ? `${formatMetric(prediction.current_u, 3)} m/s` : 'Unavailable' },
      { label: 'V', value: prediction.current_v != null ? `${formatMetric(prediction.current_v, 3)} m/s` : 'Unavailable' },
      { label: 'Model', value: `${prediction.model_id} v${prediction.model_version}` },
    ];
  }, [prediction]);

  if (!selectedLocation && !pointData && !loading && !error) {
    return null;
  }

  return (
    <aside className="ocean-inspector glass-panel" aria-live="polite">
      <div className="ocean-inspector__header">
        <div>
          <span className="ocean-inspector__eyebrow">OCEAN POINT</span>
          <h3>Inspector</h3>
        </div>
        <button type="button" className="ocean-inspector__close" onClick={onClose} aria-label="Close point inspector">
          ×
        </button>
      </div>

      {error && (
        <div className="ocean-inspector__alert">Ocean data unavailable for this location</div>
      )}

      {loading && !pointData && (
        <div className="ocean-inspector__loading">Fetching ocean state…</div>
      )}

      {!loading && pointData && (
        <>
          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">REQUESTED</div>
            <div className="ocean-inspector__row">
              <span>Lat / Lon</span>
              <strong>{formatCoordinate(requested.latitude)} / {formatCoordinate(requested.longitude)}</strong>
            </div>
          </div>

          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">MATCHED GRID</div>
            <div className="ocean-inspector__row">
              <span>Lat / Lon</span>
              <strong>{formatCoordinate(matched.latitude)} / {formatCoordinate(matched.longitude)}</strong>
            </div>
          </div>

          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">MODEL STATE</div>
            {temperatureRows.map((metric) => (
              <div key={metric.label} className="ocean-inspector__row">
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </div>

          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">CURRENT</div>
            {currentRows.map((metric) => (
              <div key={metric.label} className="ocean-inspector__row">
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </div>

          {(bathymetry || bathymetryUnavailable) && (
            <div className="ocean-inspector__section">
              <div className="ocean-inspector__section-head">SEAFLOOR</div>
              {bathymetryUnavailable ? (
                <div className="ocean-inspector__row">
                  <span>Depth</span>
                  <strong>Unavailable</strong>
                </div>
              ) : bathymetryRows.map((metric) => (
                <div key={metric.label} className="ocean-inspector__row">
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </div>
              ))}
            </div>
          )}

          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">CONTEXT</div>
            <div className="ocean-inspector__row">
              <span>Depth</span>
              <strong>{formatDepth(pointData.depth)}</strong>
            </div>
            <div className="ocean-inspector__row">
              <span>Time</span>
              <strong>{pointData.timestamp || '—'}</strong>
            </div>
          </div>

          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">SOURCE</div>
            <div className="ocean-inspector__row">
              <span>Model</span>
              <strong>{source.sourceType || 'Model'} · {source.source || 'Demo/Synthetic'}</strong>
            </div>
          </div>

          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">OBSERVATION</div>
            {observationRows.length ? observationRows.map((metric) => (
              <div key={metric.label} className="ocean-inspector__row">
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            )) : <div className="ocean-inspector__empty">No nearby observation available</div>}
          </div>

          <div className="ocean-inspector__section">
            <div className="ocean-inspector__section-head">ML PREDICTION · EXPERIMENTAL</div>
            {predictionRows.length ? predictionRows.map((metric) => (
              <div key={metric.label} className="ocean-inspector__row">
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            )) : <div className="ocean-inspector__empty">{predictionUnavailableReason === 'below_seafloor' ? 'Unavailable below the local seafloor' : predictionUnavailableReason === 'outside_coverage' ? 'Unavailable outside prototype coverage' : 'Prediction unavailable'}</div>}
          </div>
        </>
      )}

      {!pointData && !loading && selectedLocation && !error && (
        <div className="ocean-inspector__empty">Location selected. Loading ocean state…</div>
      )}
      {!pointData && bathymetryUnavailable && (
        <div className="ocean-inspector__section">
          <div className="ocean-inspector__section-head">SEAFLOOR</div>
          <div className="ocean-inspector__row">
            <span>Depth</span>
            <strong>Unavailable</strong>
          </div>
        </div>
      )}
    </aside>
  );
}
