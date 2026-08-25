import { useRef } from 'react';
import GlobeControls from '../globe/GlobeControls';
import OceanGlobe from '../globe/OceanGlobe';

function OceanMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span className="brand-orbit brand-orbit--one" />
      <span className="brand-orbit brand-orbit--two" />
      <span className="brand-core" />
    </div>
  );
}

export default function AppShell() {
  const globeRef = useRef(null);

  return (
    <main className="app-shell">
      <OceanGlobe ref={globeRef} />
      <header className="topbar glass-panel">
        <div className="brand-lockup">
          <OceanMark />
          <div className="brand-copy">
            <strong>Ocean Intelligence Explorer</strong>
            <span>Global Ocean Intelligence Platform</span>
          </div>
        </div>
        <div className="topbar-meta">
          <div className="prototype-badge"><span className="status-pulse" />Prototype Environment</div>
          <div className="phase-chip"><span>Phase 01</span><b>Global Globe</b></div>
        </div>
      </header>

      <section className="view-context glass-panel" aria-label="Current view">
        <div className="context-symbol" aria-hidden="true">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.2"/><path d="M3.8 12h16.4M12 3.8c2.2 2.3 3.3 5 3.3 8.2S14.2 17.9 12 20.2M12 3.8C9.8 6.1 8.7 8.8 8.7 12s1.1 5.9 3.3 8.2"/></svg>
        </div>
        <div><span>Default View</span><strong>Indian Ocean</strong></div>
        <i aria-hidden="true" />
      </section>

      <GlobeControls
        onHome={() => globeRef.current?.home()}
        onZoomIn={() => globeRef.current?.zoomIn()}
        onZoomOut={() => globeRef.current?.zoomOut()}
      />

      <footer className="mission-strip">
        <div><span className="mission-dot" />GLOBAL EXPLORATION</div>
        <span className="mission-separator" />
        <div>PHASE 1 · 3D GLOBE FOUNDATION</div>
        <span className="mission-spacer" />
        <div className="interaction-hint"><span>DRAG</span> rotate <span>SCROLL</span> zoom</div>
      </footer>
    </main>
  );
}
