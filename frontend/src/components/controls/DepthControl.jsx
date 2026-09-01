import './DepthControl.css';

const formatDepth = (depth) => (depth === 0 ? 'Surface / 0 m' : `${depth} m`);

export default function DepthControl({ depths, selectedDepth, onChange, loading }) {
  const selectedIndex = Math.max(0, depths.indexOf(selectedDepth));

  return (
    <section className="depth-control glass-panel" aria-label="Depth exploration">
      <div className="depth-control__header">
        <span>Depth</span>
        <strong>{formatDepth(selectedDepth)}</strong>
      </div>
      <input
        className="depth-control__slider"
        type="range"
        min="0"
        max={Math.max(depths.length - 1, 0)}
        step="1"
        value={selectedIndex}
        onChange={(event) => onChange(depths[Number(event.target.value)])}
        aria-label="Select ocean depth"
        disabled={depths.length < 2}
      />
      <div className="depth-control__ticks" aria-hidden="true">
        {depths.map((depth) => <span key={depth}>{formatDepth(depth)}</span>)}
      </div>
      {loading && <span className="depth-control__status">Updating field and point…</span>}
    </section>
  );
}
