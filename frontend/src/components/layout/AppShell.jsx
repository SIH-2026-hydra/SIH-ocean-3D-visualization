import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Math as CesiumMath,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
} from 'cesium';
import TemperatureLayer from '../layers/TemperatureLayer';
import TemperatureLegend from '../legends/TemperatureLegend';
import GlobeControls from '../globe/GlobeControls';
import OceanGlobe from '../globe/OceanGlobe';
import SelectedLocationMarker from '../globe/SelectedLocationMarker';
import OceanInspector from '../inspector/OceanInspector';
import { getOceanData, getOceanMetadata, getOceanPoint } from '../../services/api';
import { getTemperatureRange } from '../../utils/temperatureColorScale';

const DEFAULT_TEMPERATURE_TIME = '2026-08-24T00:00:00Z';
const DEMO_BOUNDS = {
  minLat: 5,
  maxLat: 30,
  minLon: 45,
  maxLon: 95,
};

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
  const [viewer, setViewer] = useState(null);
  const [temperatureData, setTemperatureData] = useState([]);
  const [temperatureMetadata, setTemperatureMetadata] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedTimestamp, setSelectedTimestamp] = useState(DEFAULT_TEMPERATURE_TIME);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [pointData, setPointData] = useState(null);
  const [pointLoading, setPointLoading] = useState(false);
  const [pointError, setPointError] = useState('');
  const selectedDepth = 0;

  useEffect(() => {
    let cancelled = false;

    async function loadMetadata() {
      try {
        const metadataResponse = await getOceanMetadata();
        const discovery = metadataResponse?.discovery;
        const timestamps = discovery?.timestamps || [DEFAULT_TEMPERATURE_TIME];
        const earliest = timestamps[0] || DEFAULT_TEMPERATURE_TIME;

        if (!cancelled) {
          setSelectedTimestamp(earliest);
        }
      } catch (loadError) {
        console.warn('Unable to fetch ocean metadata:', loadError);
      }
    }

    loadMetadata();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return undefined;

    let cancelled = false;

    async function loadTemperature() {
      setLoading(true);
      setError('');

      try {
        const result = await getOceanData({
          parameter: 'temperature',
          depth: selectedDepth,
          time: selectedTimestamp,
          minLat: DEMO_BOUNDS.minLat,
          maxLat: DEMO_BOUNDS.maxLat,
          minLon: DEMO_BOUNDS.minLon,
          maxLon: DEMO_BOUNDS.maxLon,
        });

        if (!cancelled) {
          setTemperatureData(Array.isArray(result?.data) ? result.data : []);
          setTemperatureMetadata(result?.metadata || {});
        }
      } catch (fetchError) {
        if (!cancelled) {
          setTemperatureData([]);
          setTemperatureMetadata({});
          setError(fetchError.message || 'Temperature data failed to load.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadTemperature();

    return () => {
      cancelled = true;
    };
  }, [selectedTimestamp, viewer]);

  const legendRange = useMemo(() => {
    const values = temperatureData.map((item) => Number(item.value)).filter(Number.isFinite);
    return values.length ? getTemperatureRange(values) : { min: 0, max: 0 };
  }, [temperatureData]);

  const handleGlobeSelection = async (screenPosition) => {
    const currentViewer = viewer || globeRef.current?.getViewer?.();
    if (!currentViewer || currentViewer.isDestroyed()) return;

    const scene = currentViewer.scene;
    const globe = scene.globe;
    const cartesian = scene.camera.pickEllipsoid(screenPosition, globe.ellipsoid);
    if (!cartesian) {
      setPointError('Ocean data unavailable for this location');
      return;
    }

    const cartographic = globe.ellipsoid.cartesianToCartographic(cartesian);
    const latitude = CesiumMath.toDegrees(cartographic.latitude);
    const longitude = CesiumMath.toDegrees(cartographic.longitude);

    const nextLocation = { latitude, longitude };
    setSelectedLocation(nextLocation);
    setPointError('');
    setPointLoading(true);
    setPointData(null);

    try {
      const result = await getOceanPoint({
        lat: latitude,
        lon: longitude,
        depth: selectedDepth,
        time: selectedTimestamp,
      });

      setPointData(result);
    } catch (fetchError) {
      setPointError(fetchError.message || 'Ocean data unavailable for this location');
      setPointData(null);
    } finally {
      setPointLoading(false);
    }
  };

  useEffect(() => {
    const currentViewer = viewer || globeRef.current?.getViewer?.();
    if (!currentViewer || currentViewer.isDestroyed()) return undefined;

    const handler = new ScreenSpaceEventHandler(currentViewer.scene.canvas);
    let isDragging = false;
    let dragStart = null;

    handler.setInputAction((movement) => {
      dragStart = { x: movement.position.x, y: movement.position.y };
      isDragging = false;
    }, ScreenSpaceEventType.LEFT_DOWN);

    handler.setInputAction((movement) => {
      if (!dragStart) return;
      const dx = movement.endPosition.x - dragStart.x;
      const dy = movement.endPosition.y - dragStart.y;
      isDragging = Math.hypot(dx, dy) > 8;
    }, ScreenSpaceEventType.MOUSE_MOVE);

    handler.setInputAction(() => {
      isDragging = false;
      dragStart = null;
    }, ScreenSpaceEventType.LEFT_UP);

    handler.setInputAction((click) => {
      if (isDragging) return;
      handleGlobeSelection(click.position);
    }, ScreenSpaceEventType.LEFT_CLICK);

    return () => handler.destroy();
  }, [viewer, selectedTimestamp, selectedDepth]);

  return (
    <main className="app-shell">
      <OceanGlobe ref={globeRef} onReady={setViewer} />
      {viewer && (
        <TemperatureLayer
          viewer={viewer}
          data={temperatureData}
          metadata={temperatureMetadata}
          selectedTimestamp={selectedTimestamp}
          selectedDepth={selectedDepth}
        />
      )}
      {viewer && (
        <SelectedLocationMarker
          viewer={viewer}
          location={selectedLocation}
          active={Boolean(selectedLocation) && !pointError}
        />
      )}

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
          <div className="phase-chip"><span>Phase 04</span><b>Point Inspector</b></div>
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

      {loading && (
        <div className="temperature-status temperature-status--loading glass-panel">
          Loading temperature field…
        </div>
      )}

      {error && (
        <div className="temperature-status temperature-status--error glass-panel" role="alert">
          {error}
        </div>
      )}

      {viewer && (
        <OceanInspector
          selectedLocation={selectedLocation}
          pointData={pointData}
          loading={pointLoading}
          error={pointError}
          onClose={() => {
            setSelectedLocation(null);
            setPointData(null);
            setPointError('');
          }}
        />
      )}

      <TemperatureLegend
        min={legendRange.min}
        max={legendRange.max}
        selectedDepth={selectedDepth}
        timestamp={selectedTimestamp}
        provenance={temperatureMetadata.sourceType || 'model'}
      />

      <footer className="mission-strip">
        <div><span className="mission-dot" />GLOBAL EXPLORATION</div>
        <span className="mission-separator" />
        <div>PHASE 4 · POINT INSPECTOR</div>
        <span className="mission-spacer" />
        <div className="interaction-hint"><span>DRAG</span> rotate <span>SCROLL</span> zoom</div>
      </footer>
    </main>
  );
}
