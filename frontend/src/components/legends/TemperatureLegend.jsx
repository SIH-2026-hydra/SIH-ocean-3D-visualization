import { formatTemperature, getTemperatureScaleStops } from '../../utils/temperatureColorScale';
import { getSalinityScaleStops } from '../../utils/salinityColorScale';

export default function TemperatureLegend({ min, max, selectedDepth, timestamp, provenance, parameter = 'temperature', unit = '', label }) {
  const isSalinity = parameter === 'salinity';
  const isCurrent = parameter === 'current';
  const stops = isSalinity ? getSalinityScaleStops() : getTemperatureScaleStops();
  const title = label || (isCurrent ? 'Current' : isSalinity ? 'Salinity' : parameter);

  const legendStyle = {
    position: 'absolute',
    top: '108px',
    right: '24px',
    zIndex: 12,
    width: '280px',
    maxWidth: 'calc(100vw - 32px)',
    padding: '14px 14px 12px',
    borderRadius: '16px',
    pointerEvents: 'none',
  };

  const gradientStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
    height: '14px',
    borderRadius: '999px',
    overflow: 'hidden',
    border: '1px solid rgba(189,240,255,.2)',
  };

  return (
    <div className="glass-panel" style={legendStyle} aria-live="polite">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <span style={{ fontSize: '11px', letterSpacing: '0.18em', textTransform: 'uppercase', color: '#d8eff9' }}>{title}</span>
        <span style={{ fontSize: '12px', fontWeight: 700, color: '#7fe1ff' }}>{unit}</span>
      </div>

      {isCurrent ? (
        <div style={{ color: '#a9eaf2', fontSize: '11px', lineHeight: 1.4 }}>Arrows show direction · length shows speed</div>
      ) : (
        <div style={gradientStyle} aria-hidden="true">
          {stops.map((stop) => (
            <span key={stop.stop} style={{ display: 'block', height: '100%', background: stop.color }} />
          ))}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px', color: '#edfaff', letterSpacing: '0.04em' }}>
        <span>{isCurrent ? 'Speed' : formatTemperature(min)}</span>
        <span>{isCurrent ? `${formatTemperature(max)} m/s` : formatTemperature(max)}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px', paddingTop: '2px', fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(194,219,230,.82)' }}>
        <span>Surface · 0 m</span>
        <span>{selectedDepth ?? 0} m</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px', fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(194,219,230,.82)' }}>
        <span>Timestamp</span>
        <span>{timestamp}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(153,214,238,.12)', fontSize: '10px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(194,219,230,.82)' }}>
        <span>Model data</span>
        <span>{provenance}</span>
      </div>
    </div>
  );
}
