const Icon = ({ children }) => (
  <svg viewBox="0 0 24 24" aria-hidden="true" className="control-icon">{children}</svg>
);

export default function GlobeControls({ onHome, onZoomIn, onZoomOut }) {
  return (
    <div className="globe-controls glass-panel" aria-label="Globe navigation controls">
      <button className="globe-control globe-control--home" type="button" onClick={onHome} aria-label="Reset view to the Indian Ocean" data-tooltip="Reset to Indian Ocean">
        <Icon><path d="M3.5 11.1 12 4l8.5 7.1M6.4 9.3v9.2h11.2V9.3M9.4 18.5v-5.6h5.2v5.6" /></Icon>
      </button>
      <span className="control-divider" aria-hidden="true" />
      <button className="globe-control" type="button" onClick={onZoomIn} aria-label="Zoom in" data-tooltip="Zoom in">
        <Icon><path d="M12 5v14M5 12h14" /></Icon>
      </button>
      <button className="globe-control" type="button" onClick={onZoomOut} aria-label="Zoom out" data-tooltip="Zoom out">
        <Icon><path d="M5 12h14" /></Icon>
      </button>
    </div>
  );
}
