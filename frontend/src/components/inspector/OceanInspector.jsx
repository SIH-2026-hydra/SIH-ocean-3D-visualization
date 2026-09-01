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

export default function OceanInspector({ selectedLocation, pointData, bathymetry, bathymetryUnavailable, loading, error, onClose }) {
  const requested = selectedLocation || pointData?.requestedLocation || {};
  const matched = pointData?.matchedLocation || {};
  const model = pointData?.model || {};
  const source = pointData?.source || {};

  const temperatureRows = useMemo(() => [
    { label: 'Temperature', value: model.temperature != null ? `${formatMetric(model.temperature, 2)} °C` : '—' },
    { label: 'Salinity', value: model.salinity != null ? `${formatMetric(model.salinity, 2)} PSU` : '—' },
  ], [model]);

  const currentRows = useMemo(() => [
    { label: 'Speed', value: model.currentSpeed != null ? `${formatMetric(model.currentSpeed, 3)} m/s` : '—' },
    { label: 'U', value: model.currentU != null ? `${formatMetric(model.currentU, 3)} m/s` : '—' },
    { label: 'V', value: model.currentV != null ? `${formatMetric(model.currentV, 3)} m/s` : '—' },
  ], [model]);

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
